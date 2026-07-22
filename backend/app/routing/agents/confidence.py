"""Confidence Evaluation Agent (Phase 3 §6).

Maintains a rolling success-rate table keyed by (intent, backend) in Redis,
updated by the Learning Agent from feedback. Cold-start uses sensible
priors reflecting typical model-tier strengths per intent (Phase 3 §10)
so routing is sane before any real feedback has been collected.
"""
import logging

from app.cache.redis_client import get_redis

logger = logging.getLogger("ai_gateway.confidence")

_COLD_START_PRIORS = {
    ("code", "claude"): 0.90, ("code", "gpt"): 0.88, ("code", "gemini"): 0.75, ("code", "gemma-local"): 0.55,
    ("reasoning", "gpt"): 0.90, ("reasoning", "claude"): 0.88, ("reasoning", "gemini"): 0.78, ("reasoning", "gemma-local"): 0.55,
    ("creative", "claude"): 0.90, ("creative", "gpt"): 0.85, ("creative", "gemini"): 0.78, ("creative", "gemma-local"): 0.60,
}
_DEFAULT_PRIOR = 0.80


def get_confidence(intent: str, backend_name: str) -> float:
    try:
        r = get_redis()
        key = f"confidence:{intent}:{backend_name}"
        stored = r.get(key)
        if stored is not None:
            return float(stored)
    except Exception:
        logger.debug("Redis unavailable for confidence lookup; using prior")
    return _COLD_START_PRIORS.get((intent, backend_name), _DEFAULT_PRIOR)


def update_confidence(intent: str, backend_name: str, success: bool, alpha: float = 0.1) -> None:
    """Exponential moving average update -- the Learning Agent's core operation."""
    try:
        r = get_redis()
        key = f"confidence:{intent}:{backend_name}"
        current = get_confidence(intent, backend_name)
        target = 1.0 if success else 0.0
        updated = current + alpha * (target - current)
        r.set(key, round(updated, 4))
    except Exception:
        logger.debug("Redis unavailable; skipping confidence update")
