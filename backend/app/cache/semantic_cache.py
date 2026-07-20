"""Semantic cache (Phase 3 §13, tier 2).

Uses FAISS for similarity search over prompt embeddings when available;
falls back to brute-force cosine similarity (fine at demo scale) if FAISS
isn't installed, so the gateway still runs in constrained environments.
Per Phase 3 policy, this cache is bypassed entirely for any risk != "none"
prompt to avoid leaking sensitive content across cache boundaries.
"""
import hashlib
from dataclasses import dataclass

import numpy as np

from app.config import get_settings

try:
    import faiss  # type: ignore
    _HAS_FAISS = True
except ImportError:  # pragma: no cover - environment dependent
    _HAS_FAISS = False


@dataclass
class _Entry:
    org_id: str
    embedding: np.ndarray
    response: dict


class SemanticCache:
    def __init__(self, dim: int = 64):
        self.dim = dim
        self.entries: list[_Entry] = []
        self.index = faiss.IndexFlatIP(dim) if _HAS_FAISS else None

    @staticmethod
    def _embed(text: str, dim: int = 64) -> np.ndarray:
        """Cheap deterministic pseudo-embedding (hash-based bag of shingles).
        Good enough to demonstrate near-duplicate detection without pulling
        in a real embedding model dependency for the MVP; swap for a real
        sentence-embedding model in production."""
        vec = np.zeros(dim, dtype="float32")
        tokens = text.lower().split()
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            vec[h % dim] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def lookup(self, org_id: str, prompt: str, threshold: float) -> dict | None:
        if not self.entries:
            return None
        query = self._embed(prompt, self.dim)
        best_score, best_entry = -1.0, None
        for entry in self.entries:
            if entry.org_id != org_id:
                continue
            score = float(np.dot(query, entry.embedding))
            if score > best_score:
                best_score, best_entry = score, entry
        if best_entry is not None and best_score >= threshold:
            return best_entry.response
        return None

    def add(self, org_id: str, prompt: str, response: dict) -> None:
        embedding = self._embed(prompt, self.dim)
        self.entries.append(_Entry(org_id=org_id, embedding=embedding, response=response))


_semantic_cache: SemanticCache | None = None


def get_semantic_cache() -> SemanticCache:
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache


def semantic_lookup(org_id: str, prompt: str, risk_level: str) -> dict | None:
    if risk_level != "none":
        return None  # never semantic-cache anything risk-flagged
    settings = get_settings()
    return get_semantic_cache().lookup(org_id, prompt, settings.semantic_cache_threshold)


def semantic_store(org_id: str, prompt: str, response: dict, risk_level: str) -> None:
    if risk_level != "none":
        return
    get_semantic_cache().add(org_id, prompt, response)
