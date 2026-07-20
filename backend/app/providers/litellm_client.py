"""Unified backend call wrapper (Phase 4 §providers).

Uses LiteLLM to normalize provider SDK differences behind one call
signature. When a provider's API key is not configured (common in a
hackathon demo environment with limited quota), the call runs in
deterministic MOCK MODE instead of failing outright -- this keeps the
routing engine, caching, and analytics fully demoable end-to-end even
without live credentials, per NFR-7 (graceful degradation).
"""
import logging
import time

from app.config import get_settings
from app.routing.registry import BACKENDS

logger = logging.getLogger("ai_gateway.providers")

_PROVIDER_KEY_MAP = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "google": "google_api_key",
}

_LITELLM_MODEL_MAP = {
    "claude": "claude-3-5-sonnet-20241022",
    "gpt": "gpt-4o-mini",
    "gemini": "gemini/gemini-1.5-flash",
}


class ProviderError(Exception):
    pass


def _is_mock(backend_name: str) -> bool:
    settings = get_settings()
    spec = BACKENDS[backend_name]
    if spec.is_local:
        return False  # local model attempts a real call to Ollama; falls back on connection error
    key_attr = _PROVIDER_KEY_MAP.get(spec.provider)
    return not bool(getattr(settings, key_attr, ""))


def _mock_response(backend_name: str, prompt: str) -> str:
    return (
        f"[MOCK response from {backend_name} — no API key configured for this provider. "
        f"Set the corresponding env var to get live responses.] "
        f"Echoing prompt intent for demo purposes: '{prompt[:120]}'"
    )


def call_backend(backend_name: str, messages: list[dict]) -> tuple[str, float]:
    """Returns (content, latency_ms). Raises ProviderError on failure."""
    settings = get_settings()
    prompt = messages[-1]["content"] if messages else ""
    start = time.perf_counter()

    if backend_name == "gemma-local":
        try:
            import litellm
            response = litellm.completion(
                model=f"ollama/{settings.gemma_model_name}",
                messages=messages,
                api_base=settings.gemma_base_url.replace("/v1", ""),
                timeout=15,
            )
            content = response.choices[0].message.content
        except Exception as exc:  # noqa: BLE001
            logger.warning("Local Gemma unreachable (%s); using mock response", exc)
            content = _mock_response(backend_name, prompt)
        latency_ms = (time.perf_counter() - start) * 1000
        return content, latency_ms

    if _is_mock(backend_name):
        content = _mock_response(backend_name, prompt)
        latency_ms = (time.perf_counter() - start) * 1000
        return content, latency_ms

    try:
        import litellm
        model_id = _LITELLM_MODEL_MAP[backend_name]
        response = litellm.completion(model=model_id, messages=messages, timeout=30)
        content = response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001
        logger.error("Backend %s call failed: %s", backend_name, exc)
        raise ProviderError(str(exc)) from exc

    latency_ms = (time.perf_counter() - start) * 1000
    return content, latency_ms
