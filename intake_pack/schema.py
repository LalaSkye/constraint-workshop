"""schema — Canonical field specifications for intake-pack v0.1.

Pure data-structure definitions only.  No behaviour.  No external dependencies.
"""

from typing import List

SCHEMA_VERSION = "0.1"


class IntakeRequestSchema:
    """Field specification for an intake request object.

    Fields
    ------
    actor_id        str       Caller identity.
    action_class    str       Category of the requested action.
    context         dict      Free-form metadata; must be JSON-serialisable.
    authority_scope dict      Scope key/value pairs used for rule matching.
    invariant_hash  str       SHA-256 of the invariant set in effect.
    timestamp_utc   str|None  ISO-8601 timestamp; optional, excluded from hash.
    """

    REQUIRED_FIELDS: List[str] = [
        "actor_id",
        "action_class",
        "context",
        "authority_scope",
        "invariant_hash",
    ]
    OPTIONAL_FIELDS: List[str] = ["timestamp_utc"]
    ALL_FIELDS: List[str] = REQUIRED_FIELDS + OPTIONAL_FIELDS


class IntakeVerdictSchema:
    """Field specification for an intake verdict object.

    Fields
    ------
    verdict           str   One of ALLOW, REFUSE, ESCALATE.
    reasons           list  Sorted list of reason-code strings.
    decision_hash     str   SHA-256 of the canonical decision object.
    request_hash      str   SHA-256 of the canonical request object.
    artefact_version  str   Schema version string.
    """

    VERDICT_VALUES: List[str] = ["ALLOW", "REFUSE", "ESCALATE"]
    REQUIRED_FIELDS: List[str] = [
        "verdict",
        "reasons",
        "decision_hash",
        "request_hash",
        "artefact_version",
    ]
