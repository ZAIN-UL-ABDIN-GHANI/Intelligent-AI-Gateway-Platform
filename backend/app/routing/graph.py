"""LangGraph state machine implementing the routing flow from Phase 3 §3.

Each node is a thin wrapper around the corresponding agent module, so the
graph stays declarative and every agent remains independently unit-testable.
"""
import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.providers.litellm_client import ProviderError, call_backend
from app.routing.agents.complexity import score_complexity
from app.routing.agents.confidence import update_confidence
from app.routing.agents.cost_predictor import predict_cost
from app.routing.agents.intent import detect_intent
from app.routing.agents.latency_predictor import record_latency
from app.routing.agents.risk import classify_risk
from app.routing.agents.token_predictor import estimate_input_tokens, estimate_output_tokens
from app.routing.health import get_healthy_backends, mark_degraded
from app.routing.policy import budget_pressure, eligible_backends, score_candidates
from app.routing.registry import BACKENDS

logger = logging.getLogger("ai_gateway.routing")


class RoutingState(TypedDict, total=False):
    prompt: str
    messages: list[dict]
    org_id: str
    privacy_policy: str
    current_spend: float
    monthly_limit: float
    force_backend: str | None

    intent: str
    complexity: float
    risk_level: str
    input_tokens: int
    output_tokens: int
    candidate_scores: dict
    chosen_backend: str
    reason: str

    content: str
    actual_cost: float
    latency_ms: float
    attempted_backends: list[str]
    error: str | None


def node_analyze(state: RoutingState) -> RoutingState:
    prompt = state["prompt"]
    intent = detect_intent(prompt)
    complexity = score_complexity(prompt)
    risk_level = classify_risk(prompt)
    input_tokens = estimate_input_tokens(prompt)
    output_tokens = estimate_output_tokens(intent, input_tokens)
    return {
        **state,
        "intent": intent,
        "complexity": complexity,
        "risk_level": risk_level,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def node_decide(state: RoutingState) -> RoutingState:
    healthy = get_healthy_backends()
    attempted = state.get("attempted_backends", [])

    if state.get("force_backend"):
        chosen = state["force_backend"]
        if chosen not in BACKENDS:
            return {**state, "chosen_backend": "", "reason": f"forced backend '{chosen}' does not exist", "error": "invalid_backend"}
        if chosen not in healthy:
            return {**state, "chosen_backend": "", "reason": f"forced backend '{chosen}' is degraded", "error": "backend_degraded"}
        return {
            **state,
            "chosen_backend": chosen,
            "candidate_scores": {},
            "reason": f"forced by request: force_backend={chosen}",
        }

    candidates = eligible_backends(
        intent=state["intent"],
        risk_level=state["risk_level"],
        input_tokens=state["input_tokens"],
        healthy_backends=healthy - set(attempted),
        privacy_policy=state.get("privacy_policy", "strict"),
    )

    if not candidates:
        return {**state, "chosen_backend": "", "reason": "no eligible backends remaining", "error": "all_backends_failed"}

    pressure = budget_pressure(state.get("current_spend", 0.0), state.get("monthly_limit", 100.0))
    scored = score_candidates(
        candidates=candidates,
        intent=state["intent"],
        input_tokens=state["input_tokens"],
        output_tokens=state["output_tokens"],
        budget_pressure=pressure,
        complexity=state.get("complexity", 0.0),
    )
    best = scored[0]
    reason = (
        f"routed to {best.backend}: intent={state['intent']}, risk={state['risk_level']}, "
        f"complexity={state.get('complexity', 0):.3f}, budget_pressure={pressure:.2f}, "
        f"quality={best.quality:.3f}, cost=${best.cost:.4f}, latency={best.latency:.0f}ms, "
        f"final_score={best.score}"
    )
    return {
        **state,
        "chosen_backend": best.backend,
        "candidate_scores": {c.backend: c.score for c in scored},
        "reason": reason,
    }


def node_call(state: RoutingState) -> RoutingState:
    backend = state["chosen_backend"]
    if not backend:
        return {**state, "error": "all_backends_failed"}

    attempted = state.get("attempted_backends", []) + [backend]
    try:
        content, latency_ms = call_backend(backend, state["messages"])
    except ProviderError as exc:
        logger.warning("Backend %s failed (%s: %s); marking degraded, will attempt fallback", backend, exc.error_type, exc)
        mark_degraded(backend)
        update_confidence(state["intent"], backend, success=False)
        return {**state, "attempted_backends": attempted, "error": "backend_call_failed"}

    record_latency(backend, latency_ms)
    update_confidence(state["intent"], backend, success=True)

    actual_cost = predict_cost(backend, state["input_tokens"], state["output_tokens"])

    return {
        **state,
        "attempted_backends": attempted,
        "content": content,
        "actual_cost": actual_cost,
        "latency_ms": latency_ms,
        "error": None,
    }


def should_retry(state: RoutingState) -> str:
    if state.get("error") and len(state.get("attempted_backends", [])) < len(BACKENDS):
        return "retry"
    if state.get("error"):
        return "give_up"
    return "done"


def build_graph():
    graph = StateGraph(RoutingState)
    graph.add_node("analyze", node_analyze)
    graph.add_node("decide", node_decide)
    graph.add_node("call", node_call)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "decide")
    graph.add_edge("decide", "call")
    graph.add_conditional_edges("call", should_retry, {"retry": "decide", "give_up": END, "done": END})
    return graph.compile()


_compiled_graph = None


def get_routing_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_routing(
    prompt: str,
    messages: list[dict],
    org_id: str,
    privacy_policy: str,
    current_spend: float,
    monthly_limit: float,
    force_backend: str | None = None,
) -> RoutingState:
    graph = get_routing_graph()
    initial: RoutingState = {
        "prompt": prompt,
        "messages": messages,
        "org_id": org_id,
        "privacy_policy": privacy_policy,
        "current_spend": current_spend,
        "monthly_limit": monthly_limit,
        "force_backend": force_backend,
        "attempted_backends": [],
    }
    final_state = graph.invoke(initial)
    return final_state
