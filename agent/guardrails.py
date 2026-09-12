import re

PHONE_REGEX = re.compile(r"\b(?:\+91[-.\s]?)?[6-9]\d{9}\b")
CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "system prompt",
    "disregard guidelines",
    "you are now dan",
    "bypass restrictions",
    "override rules"
]


def mask_pii(text: str) -> str:
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    return CARD_REGEX.sub("[REDACTED_CARD]", text)


def detect_injection(text: str) -> bool:
    lowered = text.lower()
    return any(p in lowered for p in INJECTION_PATTERNS)


def check_groundedness(score: float, threshold: float = 0.35) -> bool:
    return score >= threshold