"""invariant_litmus — Deterministic posture classifier.

Classifies text claims as HARD_INVARIANT (wall) or COST_CURVE (slope)
based on phrase matching and regex.  No ML.  No randomness.
No external dependencies beyond `re`.
"""

import re
from enum import Enum
from typing import NamedTuple


class Posture(Enum):
    """Claim posture."""
    HARD_INVARIANT = "hard_invariant"
    COST_CURVE = "cost_curve"
    EDGE = "edge"


class LitmusResult(NamedTuple):
    """Classification result."""
    posture: Posture
    score: float
    signals: list


# --- Signal phrases ---

_HARD_PHRASES = [
    "cannot fall below", "fundamental limit", "upper bound",
    "lower bound", "independent of hardware", "no amount of",
    "physically impossible", "thermodynamic limit",
    "shannon limit", "landauer", "planck",
]

_COST_PHRASES = [
    "can be improved", "can be optimised", "can be optimized",
    "admits mitigation", "throughput can be", "scalable",
    "scheduling", "chip upgrades", "better hardware",
]

_NEGATION_WORDS = {"not", "no", "never", "neither", "cannot", "can't"}

_QUANT_RE = re.compile(
    r"\d+(?:\.\d+)?\s*[\xd7x]\s*10[\u207b\u2070-\u2079\u00b2\u00b3\d]+"
    r"|\d+(?:\.\d+)?\s*[\xd7x]\s*10\^[\-\d]+"
    r"|kT\s*ln"
)

_HARD_WEIGHT = 0.25
_COST_WEIGHT = -0.25
_QUANT_WEIGHT = 0.15
_THRESHOLD = 0.5


def _has_negation(text: str, start: int) -> bool:
    """Check for negation within 2 words before start position."""
    prefix = text[:start].lower().split()
    window = prefix[-2:] if len(prefix) >= 2 else prefix
    return bool(set(window) & _NEGATION_WORDS)


def classify(text: str) -> LitmusResult:
    """Classify a text claim by posture.

    Returns a LitmusResult with posture, score, and detected signals.
    Score >= 0.5 means HARD_INVARIANT.  Score < 0.5 and < 0 means
    COST_CURVE.  Otherwise EDGE.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")

    lower = text.lower()
    score = 0.0
    signals = []

    for phrase in _HARD_PHRASES:
        idx = lower.find(phrase)
        if idx != -1 and not _has_negation(lower, idx):
            score += _HARD_WEIGHT
            signals.append(("hard", phrase))

    for phrase in _COST_PHRASES:
        idx = lower.find(phrase)
        if idx != -1 and not _has_negation(lower, idx):
            score += _COST_WEIGHT
            signals.append(("cost", phrase))

    if _QUANT_RE.search(text):
        score += _QUANT_WEIGHT
        signals.append(("quant", "scientific_notation"))

    if score >= _THRESHOLD:
        posture = Posture.HARD_INVARIANT
    elif score < 0:
        posture = Posture.COST_CURVE
    else:
        posture = Posture.EDGE

    return LitmusResult(posture=posture, score=round(score, 4), signals=signals)
