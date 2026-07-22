"""Backend health checks (Phase 6 GET /v1/health).

Local Gemma health is checked via a real connectivity probe; cloud
backends are considered healthy unless recently marked degraded by
a failed call.
"""
import logging
import time

import httpx

from app.cache.redis_client import get_redis
from app.config import get_settings
from app.routing.registry import BACKENDS

logger = logging.getLogger("ai_gateway.health")

_DEGRADED_TTL_SECONDS = 60

_ollama_cache: dict[str, tuple[bool, float]] = {}
_OLLAMA_CACHE_TTL = 5.0


def mark_degraded(backend_name: str) -> None:
    r = get_redis()
    r.set(f"health:degraded:{backend_name}", int(time.time()), ex=_DEGRADED_TTL_SECONDS)


def is_degraded(backend_name: str) -> bool:
    r = get_redis()
    return r.get(f"health:degraded:{backend_name}") is not None


def check_ollama_reachable() -> bool:
    now = time.monotonic()
    cached = _ollama_cache.get("status")
    if cached and (now - cached[1]) < _OLLAMA_CACHE_TTL:
        return cached[0]

    settings = get_settings()
    base = settings.gemma_base_url.replace("/v1", "")
    try:
        resp = httpx.get(f"{base}/api/tags", timeout=3.0)
        result = resp.status_code == 200
    except Exception:
        result = False

    _ollama_cache["status"] = (result, now)
    return result


def get_healthy_backends() -> set[str]:
    healthy = set()
    for name in BACKENDS:
        if is_degraded(name):
            continue
        if name == "gemma-local" and not check_ollama_reachable():
            continue
        healthy.add(name)
    return healthy


def health_snapshot() -> dict[str, str]:
    snapshot = {}
    for name in BACKENDS:
        if is_degraded(name):
            snapshot[name] = "degraded"
        elif name == "gemma-local" and not check_ollama_reachable():
            snapshot[name] = "unreachable"
        else:
            snapshot[name] = "healthy"
    return snapshot
