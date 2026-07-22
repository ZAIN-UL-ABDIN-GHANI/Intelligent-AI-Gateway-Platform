"""Exact-match response cache (Phase 3 §13, tier 1)."""
import hashlib
import json
import logging
from typing import Optional

from app.cache.redis_client import get_redis

logger = logging.getLogger("ai_gateway.cache")

_TTL_SECONDS = 60 * 60 * 24


def _hash_prompt(org_id: str, prompt: str) -> str:
    raw = f"{org_id}:{prompt.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(org_id: str, prompt: str) -> Optional[dict]:
    try:
        r = get_redis()
        key = f"cache:exact:{_hash_prompt(org_id, prompt)}"
        val = r.get(key)
        if val is None:
            return None
        return json.loads(val)
    except Exception:
        logger.debug("Cache read failed; treating as miss")
        return None


def set_cached(org_id: str, prompt: str, response: dict) -> None:
    try:
        r = get_redis()
        key = f"cache:exact:{_hash_prompt(org_id, prompt)}"
        r.set(key, json.dumps(response), ex=_TTL_SECONDS)
    except Exception:
        logger.debug("Cache write failed; skipping")
