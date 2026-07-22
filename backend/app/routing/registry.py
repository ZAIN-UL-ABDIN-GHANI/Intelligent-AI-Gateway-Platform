"""Static backend registry: pricing, context windows, provider metadata.

In production this would be seeded into the `backends` table (Phase 5) and
editable via admin API; kept as an in-memory registry here so the MVP has
zero-config startup for the demo.
"""
from dataclasses import dataclass, field
from app.config import get_settings

settings = get_settings()

@dataclass(frozen=True)
class BackendSpec:
    name: str
    provider: str
    context_window: int
    max_output_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    is_local: bool
    supports_streaming: bool = True
    supports_tools: bool = False
    model_version: str = ""


BACKENDS: dict[str, BackendSpec] = {
    "gemma-local": BackendSpec(
        name="gemma-local", provider="ollama", context_window=8192,
        max_output_tokens=2048, cost_per_1k_input=0.0, cost_per_1k_output=0.0,
        is_local=True, supports_streaming=True, supports_tools=False,
        model_version="gemma3:4b",
    ),
    "claude": BackendSpec(
        name="claude", provider="anthropic", context_window=200_000,
        max_output_tokens=8192, cost_per_1k_input=0.003, cost_per_1k_output=0.015,
        is_local=False, supports_streaming=True, supports_tools=True,
        model_version="claude-sonnet-4-20250514",
    ),
    "gpt": BackendSpec(
        name="gpt", provider="openai", context_window=128_000,
        max_output_tokens=16384, cost_per_1k_input=0.00015, cost_per_1k_output=0.0006,
        is_local=False, supports_streaming=True, supports_tools=True,
        model_version="gpt-4o-mini",
    ),
    "gemini": BackendSpec(
        name="gemini", provider="google", context_window=1_000_000,
        max_output_tokens=8192, cost_per_1k_input=0.000075, cost_per_1k_output=0.0003,
        is_local=False, supports_streaming=True, supports_tools=True,
        model_version="gemini-2.0-flash",
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
