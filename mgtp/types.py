"""mgtp.types — All MGTP types including the canonical DecisionRecord.

There is exactly one DecisionRecord implementation in this package; it lives
here.  mgtp.decision_record re-exports it for import convenience.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from authority_gate import Evidence


class RiskClass(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TransitionOutcome(str, Enum):
    APPROVED = "APPROVED"
    REFUSED = "REFUSED"
    SUPERVISED = "SUPERVISED"


@dataclass(frozen=True)
class TransitionRequest:
    transition_id: str
    risk_class: RiskClass
    irreversible: bool
    resource_identifier: str
    trust_boundary_crossed: bool
    override_token: Optional[str]
    timestamp: str  # injected; do not call a clock


@dataclass(frozen=True)
class AuthorityContext:
    actor_id: str
    authority_basis: str  # Evidence member name, e.g. "OWNER"
    tenant_id: str
    provided_evidence: Optional["Evidence"] = None


# Stable UUID5 namespace for MGTP decision IDs (reuses the DNS UUID namespace).
_DECISION_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class DecisionRecord:
    """Immutable, deterministic record of a single transition decision.

    This is the canonical and sole DecisionRecord implementation in the MGTP
    layer.  mgtp.decision_record re-exports this class; no competing version
    exists.

    Core fields (always populated):
        transition_id, outcome, authority_basis, risk_class, reason

    Extended audit fields (populated by evaluate_transition; default "" when
    not applicable):
        actor_id, tenant_id, timestamp, gate_version, context_hash

    Computed properties (derived; never stored as fields):
        reason_code     — alias for ``reason``
        canonical_bytes — deterministic UTF-8 JSON bytes (sorted keys)
        to_canonical_json — alias method for canonical_bytes
        canonical_hash  — sha256 hex digest of canonical_bytes
        content_hash    — alias for canonical_hash
        decision_id     — UUID5 derived from context_hash (empty when absent)
    """

    transition_id: str
    outcome: TransitionOutcome
    authority_basis: str
    risk_class: RiskClass
    reason: str
    # Extended audit trail (optional; defaults allow simple two-arg construction)
    actor_id: str = ""
    tenant_id: str = ""
    timestamp: str = ""
    gate_version: str = ""
    context_hash: str = ""

    # ------------------------------------------------------------------
    # Computed properties — no stored duplicates, no divergent logic
    # ------------------------------------------------------------------

    @property
    def reason_code(self) -> str:
        """Alias for ``reason``, used by registry-based evaluation paths."""
        return self.reason

    @property
    def canonical_bytes(self) -> bytes:
        """Deterministic UTF-8 JSON bytes: sorted keys, compact separators."""
        obj = {
            "authority_basis": self.authority_basis,
            "outcome": self.outcome.value,
            "reason": self.reason,
            "risk_class": self.risk_class.value,
            "transition_id": self.transition_id,
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def to_canonical_json(self) -> bytes:
        """Return canonical JSON bytes (alias for the canonical_bytes property)."""
        return self.canonical_bytes

    @property
    def canonical_hash(self) -> str:
        """sha256 hex digest (lower-case) of canonical_bytes."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()

    @property
    def content_hash(self) -> str:
        """Alias for canonical_hash."""
        return self.canonical_hash

    @property
    def decision_id(self) -> str:
        """UUID5 derived from context_hash; empty string when context_hash absent."""
        if not self.context_hash:
            return ""
        return str(uuid.uuid5(_DECISION_NS, self.context_hash))

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        *,
        transition_id: str,
        actor_id: str,
        tenant_id: str,
        authority_basis: str,
        risk_class: "str | RiskClass",
        outcome: TransitionOutcome,
        reason_code: str,
        timestamp: str,
        gate_version: str,
        context_hash: str,
    ) -> "DecisionRecord":
        """Factory for full audit-trail records (used by evaluate_transition).

        ``reason_code`` is stored as ``reason``; both attributes return the
        same value so callers can use either name.
        """
        if isinstance(risk_class, str):
            risk_class = RiskClass(risk_class)
        return cls(
            transition_id=transition_id,
            outcome=outcome,
            authority_basis=authority_basis,
            risk_class=risk_class,
            reason=reason_code,
            actor_id=actor_id,
            tenant_id=tenant_id,
            timestamp=timestamp,
            gate_version=gate_version,
            context_hash=context_hash,
        )
