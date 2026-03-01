import hashlib
import json
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
    authority_basis: str  # map to Evidence enum name e.g. "OWNER"
    tenant_id: str
    provided_evidence: Optional["Evidence"] = None


@dataclass(frozen=True)
class DecisionRecord:
    """Immutable record of a single transition decision."""
    transition_id: str
    outcome: TransitionOutcome
    authority_basis: str
    risk_class: RiskClass
    reason: str

    def to_canonical_json(self) -> bytes:
        """Return canonical JSON bytes: sorted keys, no whitespace, UTF-8."""
        obj = {
            "authority_basis": self.authority_basis,
            "outcome": self.outcome.value,
            "reason": self.reason,
            "risk_class": self.risk_class.value,
            "transition_id": self.transition_id,
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def canonical_bytes(self) -> bytes:
        """Deterministic UTF-8 serialisation; alias for to_canonical_json()."""
        return self.to_canonical_json()

    def canonical_hash(self) -> str:
        """Return sha256 hex digest (lower-case) of canonical_bytes()."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
