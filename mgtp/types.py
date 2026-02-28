import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
