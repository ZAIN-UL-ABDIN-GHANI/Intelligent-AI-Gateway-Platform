"""Complexity Analysis Agent (Phase 3 §8).

Produces a 0-1 score from cheap structural signals. Deliberately simple and
explainable rather than a black-box model, so every score is defensible in
the routing trace.
"""
import re

_MULTISTEP_MARKERS = re.compile(r"\bfirst\b.*\bthen\b|\bstep \d\b|\bfinally\b", re.IGNORECASE)
_CODE_BLOCK = re.compile(r"```")


def score_complexity(prompt: str) -> float:
    length = len(prompt)
    length_score = min(length / 2000, 1.0)  # long prompts -> more complex, cap at 2000 chars

    multistep_score = 0.3 if _MULTISTEP_MARKERS.search(prompt) else 0.0
    code_score = 0.2 if _CODE_BLOCK.search(prompt) else 0.0

    word_count = len(prompt.split())
    unique_ratio = len(set(prompt.lower().split())) / word_count if word_count else 0
    vocab_score = min(unique_ratio, 1.0) * 0.2

    score = min(1.0, 0.3 * length_score + multistep_score + code_score + vocab_score)
    return round(score, 3)
