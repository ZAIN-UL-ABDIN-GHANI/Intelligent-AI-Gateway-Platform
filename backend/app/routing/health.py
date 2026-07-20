"""Backend health checks (Phase 6 GET /v1/health).

Local Gemma health is checked via a real connectivity probe; cloud
backends are considered healthy unless recently marked degraded (e.g. by
a failed call) since we don't want a health-check API call burning quota
on every request.
"""
import time

from app.cache.redis_client import get_redis
from app.routing.registry import BACKENDS

_DEGRADED_TTL_SECONDS = 60


def mark_degraded(backend_name: str) -> None:
    r = get_redis()
    r.set(f"health:degraded:{backend_name}", int(time.time()), ex=_DEGRADED_TTL_SECONDS)


def is_degraded(backend_name: str) -> bool:
    r = get_redis()
    return r.get(f"health:degraded:{backend_name}") is not None


def get_healthy_backends() -> set[str]:
    return {name for name in BACKENDS if not is_degraded(name)}


def health_snapshot() -> dict[str, str]:
    return {name: ("degraded" if is_degraded(name) else "healthy") for name in BACKENDS}
