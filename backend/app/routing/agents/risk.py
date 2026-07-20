"""Risk / PII Classification Agent (Phase 3 §7).

Runs entirely locally (regex-based for MVP) so sensitive content is never
sent anywhere -- including to a cloud classifier -- before the risk
decision itself has been made. Swappable for a proper local NER model
(e.g. presidio) without changing the router's interface.
"""
import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
_SECRET_KEY = re.compile(r"\b(sk-|api[_-]?key|secret|password)\b", re.IGNORECASE)

HIGH_RISK_PATTERNS = [_SSN, _CREDIT_CARD, _SECRET_KEY]
LOW_RISK_PATTERNS = [_EMAIL, _PHONE]


def classify_risk(prompt: str) -> str:
    for pattern in HIGH_RISK_PATTERNS:
        if pattern.search(prompt):
            return "high"
    for pattern in LOW_RISK_PATTERNS:
        if pattern.search(prompt):
            return "low"
    return "none"
