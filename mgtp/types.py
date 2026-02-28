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
    """Immutable record of an MGTP transition decision."""

    transition_id: str
    outcome: TransitionOutcome
    risk_class: RiskClass
    actor_id: str
    authority_basis: str
    timestamp: str

    def canonical_bytes(self) -> bytes:
        """Return deterministic UTF-8 bytes for this record.

        Rules:
        - Explicit field ordering (alphabetical)
        - Sorted keys in JSON serialisation
        - No reliance on __repr__
        - No unordered set serialisation
        """
        obj = {
            "actor_id": self.actor_id,
            "authority_basis": self.authority_basis,
            "outcome": self.outcome.value,
            "risk_class": self.risk_class.value,
            "timestamp": self.timestamp,
            "transition_id": self.transition_id,
        }
        return json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    def canonical_hash(self) -> str:
        """Return sha256 hex digest (lower-case) of canonical_bytes()."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
