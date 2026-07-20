"""Cost Prediction Agent (Phase 3 §6)."""
from app.routing.registry import BACKENDS


def predict_cost(backend_name: str, input_tokens: int, output_tokens: int) -> float:
    spec = BACKENDS[backend_name]
    cost = (input_tokens / 1000) * spec.cost_per_1k_input + (output_tokens / 1000) * spec.cost_per_1k_output
    return round(cost, 6)
