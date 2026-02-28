"""decision_record — Deterministic, immutable record of a transition decision."""

import hashlib
import json
import uuid
from dataclasses import dataclass

from mgtp.types import TransitionOutcome

# Stable UUID5 namespace for MGTP decision IDs.
# This reuses the standard DNS UUID namespace as a fixed, well-known seed value.
_DECISION_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


@dataclass(frozen=True)
class DecisionRecord:
    """Immutable record of a single transition decision.

    decision_id is derived deterministically from context_hash via uuid5.
    canonical_bytes and content_hash are computed at construction and stored.
    """

    transition_id: str
    actor_id: str
    tenant_id: str
    authority_basis: str
    risk_class: str
    outcome: TransitionOutcome
    reason_code: str
    timestamp: str
    gate_version: str
    context_hash: str
    decision_id: str
    canonical_bytes: bytes
    content_hash: str

    @staticmethod
    def build(
        *,
        transition_id: str,
        actor_id: str,
        tenant_id: str,
        authority_basis: str,
        risk_class: str,
        outcome: TransitionOutcome,
        reason_code: str,
        timestamp: str,
        gate_version: str,
        context_hash: str,
    ) -> "DecisionRecord":
        """Construct a DecisionRecord with all derived fields computed."""
        decision_id = str(uuid.uuid5(_DECISION_NS, context_hash))

        payload = {
            "transition_id": transition_id,
            "actor_id": actor_id,
            "tenant_id": tenant_id,
            "authority_basis": authority_basis,
            "risk_class": risk_class,
            "outcome": outcome.value,
            "reason_code": reason_code,
            "timestamp": timestamp,
            "gate_version": gate_version,
            "context_hash": context_hash,
            "decision_id": decision_id,
        }
        canonical_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        content_hash = hashlib.sha256(canonical_bytes).hexdigest()

        return DecisionRecord(
            transition_id=transition_id,
            actor_id=actor_id,
            tenant_id=tenant_id,
            authority_basis=authority_basis,
            risk_class=risk_class,
            outcome=outcome,
            reason_code=reason_code,
            timestamp=timestamp,
            gate_version=gate_version,
            context_hash=context_hash,
            decision_id=decision_id,
            canonical_bytes=canonical_bytes,
            content_hash=content_hash,
        )
