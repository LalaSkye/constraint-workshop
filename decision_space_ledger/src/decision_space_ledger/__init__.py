"""Decision-Space Diff Ledger — inspection utility for versioned decision-space snapshots.

Inspection only.  No modification of enforcement, gating, authority, or runtime logic.

Public API::

    from decision_space_ledger import validate, canonicalise, canonical_hash, diff

    snapshot = {
        "version": "v1",
        "variables": ["A", "B"],
        "allowed_transitions": [{"from": "A", "to": "B"}],
        "exclusions": [],
        "reason_code_families": {"approval": ["MANUAL", "AUTO"]},
    }
    validate(snapshot)
    h = canonical_hash(snapshot)
    delta = diff(snapshot, other_snapshot)
"""

from .canonicalise import canonical_hash, canonicalise
from .diff import diff
from .schema import SCHEMA, validate

__version__ = "0.1.0"

__all__ = [
    "SCHEMA",
    "canonicalise",
    "canonical_hash",
    "diff",
    "validate",
]
