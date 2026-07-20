"""Intent Detection Agent (Phase 3 §9).

MVP implementation: keyword/pattern heuristics rather than a trained
classifier, so it's fast, dependency-free, and fully unit-testable.
Swappable later for an embedding-similarity or fine-tuned classifier
without touching any other agent.
"""
import re

_CODE_PATTERNS = re.compile(r"```|def |class |function\s*\(|import |SELECT |<html", re.IGNORECASE)
_REASONING_PATTERNS = re.compile(r"\bwhy\b|\bexplain\b|\bprove\b|step by step|reasoning|analyze", re.IGNORECASE)
_CREATIVE_PATTERNS = re.compile(r"\bstory\b|\bpoem\b|\bwrite a\b.*\b(tale|novel|song)\b|imagine", re.IGNORECASE)
_SUMMARY_PATTERNS = re.compile(r"\bsummarize\b|\btl;?dr\b|shorten|condense", re.IGNORECASE)
_EXTRACTION_PATTERNS = re.compile(r"\bextract\b|\bparse\b|list all|find all", re.IGNORECASE)


def detect_intent(prompt: str) -> str:
    if _CODE_PATTERNS.search(prompt):
        return "code"
    if _SUMMARY_PATTERNS.search(prompt):
        return "summarization"
    if _EXTRACTION_PATTERNS.search(prompt):
        return "extraction"
    if _CREATIVE_PATTERNS.search(prompt):
        return "creative"
    if _REASONING_PATTERNS.search(prompt):
        return "reasoning"
    if prompt.strip().endswith("?"):
        return "qa"
    return "chat"
