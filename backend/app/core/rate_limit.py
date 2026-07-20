"""Simple fixed-window rate limiter (Phase 6 §14).

A true token bucket is a stretch goal; a fixed 60s window counter gives
the same practical protection with far less code, which matters at
hackathon scope.
"""
from app.cache.redis_client import get_redis
from app.config import get_settings


def check_rate_limit(api_key_id: str) -> bool:
    """Returns True if the request is allowed, False if rate-limited."""
    settings = get_settings()
    r = get_redis()
    key = f"ratelimit:{api_key_id}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, 60)
    return count <= settings.default_rate_limit_per_min
