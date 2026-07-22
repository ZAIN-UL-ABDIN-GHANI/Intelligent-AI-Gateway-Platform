"""Latency Prediction Agent (Phase 3 §6).

Maintains a rolling average observed latency per backend in Redis. Falls
back to a static prior (local model assumed fastest, biggest cloud models
assumed slower) when no history exists yet -- important for demo cold-start.
"""
import logging

from app.cache.redis_client import get_redis

logger = logging.getLogger("ai_gateway.latency")

_DEFAULT_LATENCY_MS = {
    "gemma-local": 400,
    "gemini": 900,
    "claude": 1200,
    "gpt": 1300,
}

_WINDOW = 20


def predict_latency(backend_name: str) -> float:
    try:
        r = get_redis()
        key = f"latency:{backend_name}"
        values = r.lrange(key, 0, -1)
        if not values:
            return float(_DEFAULT_LATENCY_MS.get(backend_name, 1000))
        nums = [float(v) for v in values]
        return sum(nums) / len(nums)
    except Exception:
        logger.debug("Redis unavailable for latency prediction; using default")
        return float(_DEFAULT_LATENCY_MS.get(backend_name, 1000))


def record_latency(backend_name: str, latency_ms: float) -> None:
    try:
        r = get_redis()
        key = f"latency:{backend_name}"
        r.lpush(key, latency_ms)
        r.ltrim(key, 0, _WINDOW - 1)
    except Exception:
        logger.debug("Redis unavailable; skipping latency record")
