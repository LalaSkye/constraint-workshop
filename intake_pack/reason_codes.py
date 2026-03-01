"""reason_codes — Canonical reason-code families for intake-pack v0.1.

Each Enum groups the reason-code strings that may accompany a given verdict
class.  Values match the strings emitted by the commit_gate engine so that
consumers can compare by value without a hard engine dependency.

No logic.  No external dependencies.
"""

from enum import Enum
from typing import Dict, Type


class AllowFamily(Enum):
    """Reason codes that accompany an ALLOW verdict."""

    ALLOWLIST_MATCH = "allowlist_match"
    EXPLICIT_GRANT = "explicit_grant"


class RefuseFamily(Enum):
    """Reason codes that accompany a REFUSE verdict."""

    DENYLIST_MATCH = "denylist_match"
    DEFAULT_REFUSE = "default_refuse"
    MISSING_EVIDENCE = "missing_evidence"


class EscalateFamily(Enum):
    """Reason codes that accompany an ESCALATE verdict."""

    ESCALATION_MATCH = "escalation_match"
    SCOPE_AMBIGUOUS = "scope_ambiguous"


# Maps a verdict string to its corresponding reason-code family.
VERDICT_FAMILY: Dict[str, Type[Enum]] = {
    "ALLOW": AllowFamily,
    "REFUSE": RefuseFamily,
    "ESCALATE": EscalateFamily,
}
