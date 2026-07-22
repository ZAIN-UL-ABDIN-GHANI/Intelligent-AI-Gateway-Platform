"""Unified backend call wrapper (Phase 4 §providers).

Uses LiteLLM to normalize provider SDK differences behind one call
signature. When a provider's API key is not configured, the call runs in
deterministic MOCK MODE instead of failing outright -- this keeps the
routing engine, caching, and analytics demoable end-to-end even without
live credentials, per NFR-7 (graceful degradation).
"""
import logging
import time
from collections.abc import Generator
from typing import Any

import litellm
from litellm.exceptions import (
    APIConnectionError,
    AuthenticationError,
    RateLimitError,
    Timeout,
)

from app.config import get_settings
from app.routing.registry import BACKENDS

logger = logging.getLogger("ai_gateway.providers")

# --- LiteLLM global configuration ---
litellm.drop_params = True
litellm.set_verbose = False

_PROVIDER_KEY_MAP = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "google": "google_api_key",
}

_LITELLM_MODEL_MAP: dict[str, str] = {
    "claude": "claude-sonnet-4-20250514",
    "gpt": "gpt-4o-mini",
    "gemini": "gemini/gemini-2.0-flash",
}

_RETRY_DELAY_BASE = 0.5


def _get_timeout(backend_name: str) -> int:
    settings = get_settings()
    timeout_map = {
        "gemma-local": settings.provider_timeout_ollama,
        "claude": settings.provider_timeout_anthropic,
        "gpt": settings.provider_timeout_openai,
        "gemini": settings.provider_timeout_google,
    }
    return timeout_map.get(backend_name, 30)


def _get_max_retries() -> int:
    return get_settings().provider_max_retries


class ProviderError(Exception):
    """Raised when a provider call fails after retries."""

    def __init__(self, message: str, provider: str = "", error_type: str = "unknown"):
        self.provider = provider
        self.error_type = error_type
        super().__init__(message)


def _is_mock(backend_name: str) -> bool:
    settings = get_settings()
    spec = BACKENDS[backend_name]
    if spec.is_local:
        return False
    key_attr = _PROVIDER_KEY_MAP.get(spec.provider)
    if not key_attr:
        return True
    key_value = getattr(settings, key_attr, "")
    return not bool(key_value and key_value.strip())


def _mock_response(backend_name: str, prompt: str) -> str:
    spec = BACKENDS[backend_name]
    env_var = _PROVIDER_KEY_MAP.get(spec.provider, "UNKNOWN").upper()
    return (
        f"[MOCK — {backend_name}] No API key configured. "
        f"Set {env_var} to enable live responses. "
        f"Echo: '{prompt[:100]}'"
    )


def _classify_error(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "auth_error"
    if isinstance(exc, RateLimitError):
        return "rate_limited"
    if isinstance(exc, Timeout):
        return "timeout"
    if isinstance(exc, APIConnectionError):
        return "connection_error"
    return "provider_error"


def _is_retryable(exc: Exception) -> bool:
    return isinstance(exc, (RateLimitError, Timeout, APIConnectionError))


def _call_with_retry(
    model: str,
    messages: list[dict],
    timeout: int,
    backend_name: str,
    **kwargs: Any,
) -> Any:
    max_retries = _get_max_retries()
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return litellm.completion(
                model=model,
                messages=messages,
                timeout=timeout,
                **kwargs,
            )
        except (RateLimitError, Timeout, APIConnectionError) as exc:
            last_exc = exc
            if attempt < max_retries:
                delay = _RETRY_DELAY_BASE * (2 ** attempt)
                logger.warning(
                    "%s attempt %d/%d failed (%s: %s), retrying in %.1fs",
                    backend_name, attempt + 1, max_retries + 1,
                    type(exc).__name__, exc, delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "%s exhausted %d retries: %s", backend_name, max_retries + 1, exc
                )
        except AuthenticationError as exc:
            logger.error("%s auth failed — check API key: %s", backend_name, exc)
            raise ProviderError(
                f"{backend_name} authentication failed. Verify your API key.",
                provider=backend_name,
                error_type="auth_error",
            ) from exc
        except Exception as exc:
            logger.error("%s unexpected error: %s: %s", backend_name, type(exc).__name__, exc)
            raise ProviderError(
                f"{backend_name} call failed: {type(exc).__name__}: {exc}",
                provider=backend_name,
                error_type=_classify_error(exc),
            ) from exc

    raise ProviderError(
        f"{backend_name} failed after {max_retries + 1} attempts: {last_exc}",
        provider=backend_name,
        error_type=_classify_error(last_exc) if last_exc else "unknown",
    ) from last_exc


def get_provider_status() -> dict[str, dict[str, Any]]:
    """Return live/mock status for each backend. Used by health endpoint."""
    result = {}
    for name, spec in BACKENDS.items():
        is_mock = _is_mock(name)
        result[name] = {
            "provider": spec.provider,
            "mode": "mock" if is_mock else "live",
            "model": _LITELLM_MODEL_MAP.get(name, f"ollama/{get_settings().gemma_model_name}"),
        }
    return result


def call_backend(backend_name: str, messages: list[dict]) -> tuple[str, float]:
    """Returns (content, latency_ms). Raises ProviderError on failure."""
    settings = get_settings()
    prompt = messages[-1]["content"] if messages else ""
    timeout = _get_timeout(backend_name)
    start = time.perf_counter()

    if backend_name not in BACKENDS:
        raise ProviderError(
            f"Unknown backend '{backend_name}'",
            provider=backend_name,
            error_type="config_error",
        )

    if backend_name == "gemma-local":
        try:
            response = _call_with_retry(
                model=f"ollama/{settings.gemma_model_name}",
                messages=messages,
                timeout=timeout,
                backend_name=backend_name,
                api_base=settings.gemma_base_url.replace("/v1", ""),
            )
            content = response.choices[0].message.content
        except ProviderError:
            logger.warning("Local Gemma unreachable; returning mock response")
            content = _mock_response(backend_name, prompt)
        latency_ms = (time.perf_counter() - start) * 1000
        return content, latency_ms

    if _is_mock(backend_name):
        logger.debug("%s running in mock mode (no API key)", backend_name)
        content = _mock_response(backend_name, prompt)
        latency_ms = (time.perf_counter() - start) * 1000
        return content, latency_ms

    model_id = _LITELLM_MODEL_MAP.get(backend_name)
    if not model_id:
        raise ProviderError(
            f"No model mapping for backend '{backend_name}'",
            provider=backend_name,
            error_type="config_error",
        )

    response = _call_with_retry(
        model=model_id,
        messages=messages,
        timeout=timeout,
        backend_name=backend_name,
    )
    content = response.choices[0].message.content
    latency_ms = (time.perf_counter() - start) * 1000
    return content, latency_ms


def call_backend_stream(
    backend_name: str, messages: list[dict]
) -> Generator[str, None, None]:
    """Yields content chunks. Raises ProviderError on failure."""
    settings = get_settings()
    prompt = messages[-1]["content"] if messages else ""
    timeout = _get_timeout(backend_name)

    if backend_name not in BACKENDS:
        raise ProviderError(
            f"Unknown backend '{backend_name}'",
            provider=backend_name,
            error_type="config_error",
        )

    if backend_name == "gemma-local":
        model = f"ollama/{settings.gemma_model_name}"
        api_base = settings.gemma_base_url.replace("/v1", "")
    elif _is_mock(backend_name):
        mock = _mock_response(backend_name, prompt)
        for word in mock.split(" "):
            yield word + " "
        return
    else:
        model = _LITELLM_MODEL_MAP.get(backend_name)
        if not model:
            raise ProviderError(
                f"No model mapping for backend '{backend_name}'",
                provider=backend_name,
                error_type="config_error",
            )
        api_base = None

    try:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "timeout": timeout,
            "stream": True,
        }
        if api_base:
            kwargs["api_base"] = api_base

        response = litellm.completion(**kwargs)
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except AuthenticationError as exc:
        raise ProviderError(
            f"{backend_name} authentication failed during stream",
            provider=backend_name,
            error_type="auth_error",
        ) from exc
    except (RateLimitError, Timeout, APIConnectionError) as exc:
        raise ProviderError(
            f"{backend_name} stream failed: {type(exc).__name__}: {exc}",
            provider=backend_name,
            error_type=_classify_error(exc),
        ) from exc
    except Exception as exc:
        raise ProviderError(
            f"{backend_name} stream error: {type(exc).__name__}: {exc}",
            provider=backend_name,
            error_type=_classify_error(exc),
        ) from exc
