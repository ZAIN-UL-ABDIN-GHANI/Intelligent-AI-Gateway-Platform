"""Exact-match response cache (Phase 3 §13, tier 1)."""
import hashlib
import json
from typing import Optional

from app.cache.redis_client import get_redis

_TTL_SECONDS = 60 * 60 * 24  # 24h


def _hash_prompt(org_id: str, prompt: str) -> str:
    raw = f"{org_id}:{prompt.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(org_id: str, prompt: str) -> Optional[dict]:
    r = get_redis()
    key = f"cache:exact:{_hash_prompt(org_id, prompt)}"
    val = r.get(key)
    if val is None:
        return None
    return json.loads(val)


def set_cached(org_id: str, prompt: str, response: dict) -> None:
    r = get_redis()
    key = f"cache:exact:{_hash_prompt(org_id, prompt)}"
    r.set(key, json.dumps(response), ex=_TTL_SECONDS)
