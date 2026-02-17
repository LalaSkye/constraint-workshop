"""authority_gate — Monotonic evidence-ordered access control.

A deterministic gate that compares a provided evidence level
against a required level.  If evidence is insufficient, access
is denied.  No optimisation.  No callbacks.  No orchestration.
"""

from enum import IntEnum


class Evidence(IntEnum):
    """Totally ordered evidence levels."""
    NONE = 0
    USER = 1
    OWNER = 2
    ADMIN = 3


class Decision(IntEnum):
    """Gate outcomes."""
    DENY = 0
    ALLOW = 1


class AuthorityGate:
    """Evidence-ordered access gate.

    Invariants:
        - required_level is fixed at construction.
        - check() is pure: same inputs produce same output.
        - Evidence ordering is total and monotonic.
        - No side effects.  No logging.  No state mutation.
    """

    def __init__(self, required_level: Evidence) -> None:
        if not isinstance(required_level, Evidence):
            raise TypeError(f"required_level must be Evidence, got {type(required_level).__name__}")
        self._required = required_level

    @property
    def required_level(self) -> Evidence:
        """The minimum evidence level this gate demands."""
        return self._required

    def check(self, provided: Evidence) -> Decision:
        """Evaluate access.

        Returns ALLOW if provided >= required_level, else DENY.
        """
        if not isinstance(provided, Evidence):
            raise TypeError(f"provided must be Evidence, got {type(provided).__name__}")
        if provided >= self._required:
            return Decision.ALLOW
        return Decision.DENY
