"""Redis client singleton.

Falls back to an in-memory fake if Redis is unreachable, so the demo never
hard-fails just because the cache/stats layer is down (NFR-7, graceful
degradation). Not a substitute for real Redis in production -- state won't
be shared across workers in fallback mode.
"""
import logging
from typing import Optional

import redis

from app.config import get_settings

logger = logging.getLogger("ai_gateway.redis")
_client: Optional["_RedisLike"] = None


class _InMemoryFakeRedis:
    """Minimal subset of the redis-py API used by this project."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._lists: dict[str, list[str]] = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ex=None):
        self._store[key] = str(value)

    def incr(self, key, amount=1):
        val = int(self._store.get(key, 0)) + amount
        self._store[key] = str(val)
        return val

    def expire(self, key, seconds):
        pass

    def lpush(self, key, value):
        self._lists.setdefault(key, []).insert(0, str(value))

    def lrange(self, key, start, end):
        lst = self._lists.get(key, [])
        if end == -1:
            return lst[start:]
        return lst[start:end + 1]

    def ltrim(self, key, start, end):
        lst = self._lists.get(key, [])
        self._lists[key] = lst[start:end + 1] if end != -1 else lst[start:]


_RedisLike = redis.Redis


def get_redis():
    global _client
    if _client is not None:
        return _client
    settings = get_settings()
    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1)
        client.ping()
        _client = client
        logger.info("Connected to Redis at %s", settings.redis_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis unavailable (%s); using in-memory fallback", exc)
        _client = _InMemoryFakeRedis()
    return _client
