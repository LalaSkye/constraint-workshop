import dataclasses
import hashlib
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
    """Immutable record of a single MGTP transition decision.

    Canonical serialisation: sorted-key JSON, no whitespace, UTF-8.
    decision_hash: sha256 hex (lower-case) of canonical_bytes.
    All fields are plain strings/bools so serialisation is deterministic.
    """

    transition_id: str
    risk_class: str          # RiskClass value
    irreversible: bool
    resource_identifier: str
    trust_boundary_crossed: bool
    override_token: Optional[str]
    timestamp: str           # injected; do not call a clock
    actor_id: str
    authority_basis: str
    tenant_id: str
    verdict: str             # TransitionOutcome value

    def canonical_bytes(self) -> bytes:
        """Return canonical JSON bytes (sorted keys, no whitespace, UTF-8)."""
        return json.dumps(
            dataclasses.asdict(self),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    def decision_hash(self) -> str:
        """Return sha256 hex digest (lower-case) of canonical_bytes."""
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
