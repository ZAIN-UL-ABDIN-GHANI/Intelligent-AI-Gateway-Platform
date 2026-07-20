"""Static backend registry: pricing, context windows, provider metadata.

In production this would be seeded into the `backends` table (Phase 5) and
editable via admin API; kept as an in-memory registry here so the MVP has
zero-config startup for the demo.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class BackendSpec:
    name: str
    provider: str
    context_window: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    is_local: bool


BACKENDS: dict[str, BackendSpec] = {
    "gemma-local": BackendSpec(
        name="gemma-local", provider="ollama", context_window=8192,
        cost_per_1k_input=0.0, cost_per_1k_output=0.0, is_local=True,
    ),
    "claude": BackendSpec(
        name="claude", provider="anthropic", context_window=200_000,
        cost_per_1k_input=0.003, cost_per_1k_output=0.015, is_local=False,
    ),
    "gpt": BackendSpec(
        name="gpt", provider="openai", context_window=128_000,
        cost_per_1k_input=0.0025, cost_per_1k_output=0.010, is_local=False,
    ),
    "gemini": BackendSpec(
        name="gemini", provider="google", context_window=1_000_000,
        cost_per_1k_input=0.00125, cost_per_1k_output=0.005, is_local=False,
    ),
}

# Intent -> ordered quality-preference list (Phase 3 §10)
INTENT_AFFINITY: dict[str, list[str]] = {
    "chat": ["gemma-local", "gemini", "claude", "gpt"],
    "extraction": ["gemma-local", "gemini", "claude", "gpt"],
    "summarization": ["gemma-local", "gemini", "claude", "gpt"],
    "code": ["claude", "gpt", "gemini", "gemma-local"],
    "reasoning": ["gpt", "claude", "gemini", "gemma-local"],
    "creative": ["claude", "gpt", "gemini", "gemma-local"],
    "qa": ["gemma-local", "gemini", "claude", "gpt"],
}
