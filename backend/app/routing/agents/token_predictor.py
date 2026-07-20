"""Token Prediction Agent (Phase 3 §5).

Input tokens: approximated via a chars/4 heuristic (close enough across
providers for routing purposes without pulling in per-provider tokenizers).
Output tokens: predicted from intent-specific historical averages, with a
simple length-scaling factor.
"""

_OUTPUT_TOKEN_PRIORS = {
    "chat": 80,
    "qa": 60,
    "extraction": 100,
    "summarization": 150,
    "code": 300,
    "reasoning": 250,
    "creative": 400,
}


def estimate_input_tokens(prompt: str) -> int:
    return max(1, len(prompt) // 4)


def estimate_output_tokens(intent: str, input_tokens: int) -> int:
    base = _OUTPUT_TOKEN_PRIORS.get(intent, 100)
    # scale slightly with input size, capped, to reflect longer prompts -> longer answers
    scaled = base + min(input_tokens // 10, 200)
    return scaled
