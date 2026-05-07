"""status_envelope — Standardised status wrapper for intake-pack v0.1.

A pure data container.  No I/O.  No external dependencies.
"""

from typing import Any, List, NamedTuple, Optional

ENVELOPE_VERSION = "0.1"


class StatusEnvelope(NamedTuple):
    """Standardised response wrapper.

    Fields
    ------
    ok               bool         True if the operation succeeded without error.
    status           str          Verdict tag: ALLOW, REFUSE, or ESCALATE.
    reason_codes     List[str]    Sorted list of reason-code strings.
    payload          Any|None     Inner result object; None on error.
    envelope_version str          Schema version for this envelope.
    error            str|None     Error message; populated only when ok is False.
    """

    ok: bool
    status: str
    reason_codes: List[str]
    payload: Optional[Any]
    envelope_version: str = ENVELOPE_VERSION
    error: Optional[str] = None
