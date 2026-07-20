"""Routing policy: eligibility filtering + weighted scoring (Phase 3 §4)."""
from dataclasses import dataclass

from app.config import get_settings
from app.routing.agents.confidence import get_confidence
from app.routing.agents.cost_predictor import predict_cost
from app.routing.agents.latency_predictor import predict_latency
from app.routing.registry import BACKENDS, INTENT_AFFINITY


@dataclass
class CandidateScore:
    backend: str
    quality: float
    cost: float
    latency: float
    score: float


def eligible_backends(
    intent: str,
    risk_level: str,
    input_tokens: int,
    healthy_backends: set[str],
    privacy_policy: str = "strict",
) -> list[str]:
    candidates = INTENT_AFFINITY.get(intent, list(BACKENDS.keys()))
    result = []
    for name in candidates:
        spec = BACKENDS[name]
        if name not in healthy_backends:
            continue
        if input_tokens > spec.context_window:
            continue
        if risk_level == "high" and privacy_policy == "strict" and not spec.is_local:
            continue
        result.append(name)
    # Guarantee at least one eligible backend: fall back to any local backend for high risk
    if not result and risk_level == "high":
        result = [n for n in BACKENDS if BACKENDS[n].is_local and n in healthy_backends]
    return result


def score_candidates(
    candidates: list[str],
    intent: str,
    input_tokens: int,
    output_tokens: int,
    budget_pressure: float,
    weights: dict | None = None,
) -> list[CandidateScore]:
    settings = get_settings()
    w = weights or {
        "quality": settings.default_weight_quality,
        "cost": settings.default_weight_cost,
        "latency": settings.default_weight_latency,
        "budget": settings.default_weight_budget,
    }

    raw_costs = {b: predict_cost(b, input_tokens, output_tokens) for b in candidates}
    raw_latencies = {b: predict_latency(b) for b in candidates}
    max_cost = max(raw_costs.values()) or 1e-9
    max_latency = max(raw_latencies.values()) or 1e-9

    scored = []
    for b in candidates:
        quality = get_confidence(intent, b)
        norm_cost = raw_costs[b] / max_cost
        norm_latency = raw_latencies[b] / max_latency
        is_cheap_bonus = (1.0 - norm_cost) * budget_pressure
        score = (
            w["quality"] * quality
            + w["cost"] * (1 - norm_cost)
            + w["latency"] * (1 - norm_latency)
            + w["budget"] * is_cheap_bonus
        )
        scored.append(CandidateScore(backend=b, quality=quality, cost=raw_costs[b], latency=raw_latencies[b], score=round(score, 4)))

    scored.sort(key=lambda c: c.score, reverse=True)
    return scored


def budget_pressure(current_spend: float, monthly_limit: float) -> float:
    if monthly_limit <= 0:
        return 0.0
    ratio = current_spend / monthly_limit
    return max(0.0, min(1.0, ratio))
