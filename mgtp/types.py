import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


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
    """Immutable, canonical artefact recording an MGTP evaluation decision.

    Fields are sorted alphabetically in the canonical representation to
    guarantee byte-for-byte stability across Python versions and runs.
    """

    transition_id: str
    verdict: TransitionOutcome
    reasons: Tuple[str, ...]  # must be pre-sorted by caller
    decision_time: str        # ISO-8601 timestamp; injected, never generated here
    authority_basis: str

    def canonical_bytes(self) -> bytes:
        """Return deterministic UTF-8 JSON bytes (sorted keys, no whitespace)."""
        obj = {
            "authority_basis": self.authority_basis,
            "decision_time": self.decision_time,
            "reasons": list(self.reasons),
            "transition_id": self.transition_id,
            "verdict": self.verdict.value,
        }
        return json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    @property
    def decision_hash(self) -> str:
        """SHA-256 hex digest (lower-case) of canonical_bytes()."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
