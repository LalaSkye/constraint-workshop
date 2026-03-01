"""evaluate_transition — Core MGTP decision engine."""

import hashlib
import json

from authority_gate import AuthorityGate, Decision, Evidence
from mgtp.decision_record import DecisionRecord
from mgtp.types import AuthorityContext, RiskClass, TransitionOutcome, TransitionRequest

_HIGH_RISK = {RiskClass.HIGH, RiskClass.CRITICAL}


def _compute_context_hash(request: TransitionRequest, context: AuthorityContext) -> str:
    """Deterministic sha256 over the canonical representation of (request, context)."""
    payload = {
        "transition_id": request.transition_id,
        "risk_class": request.risk_class.value,
        "irreversible": request.irreversible,
        "resource_identifier": request.resource_identifier,
        "trust_boundary_crossed": request.trust_boundary_crossed,
        "override_token": request.override_token,
        "timestamp": request.timestamp,
        "actor_id": context.actor_id,
        "authority_basis": context.authority_basis,
        "tenant_id": context.tenant_id,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def evaluate_transition(
    request: TransitionRequest,
    context: AuthorityContext,
    registry: dict,
) -> DecisionRecord:
    """Evaluate a transition request against the registry and authority context.

    Decision logic (in order):
    1. Transition not in registry -> REFUSED / UNDECLARED_TRANSITION
    2. Authority insufficient      -> REFUSED / AUTHORITY_INVALID
    3. HIGH/CRITICAL, no override  -> REFUSED / SUPERVISION_REQUIRED
    4. override_token present      -> SUPERVISED / OVERRIDE_TOKEN_PRESENT
    5. Otherwise                   -> APPROVED / APPROVED
    """
    context_hash = _compute_context_hash(request, context)

    def _make_record(outcome: TransitionOutcome, reason_code: str, gate_version: str = "") -> DecisionRecord:
        return DecisionRecord.build(
            transition_id=request.transition_id,
            actor_id=context.actor_id,
            tenant_id=context.tenant_id,
            authority_basis=context.authority_basis,
            risk_class=request.risk_class.value,
            outcome=outcome,
            reason_code=reason_code,
            timestamp=request.timestamp,
            gate_version=gate_version,
            context_hash=context_hash,
        )

    # 1. Check registry membership.
    if request.transition_id not in registry:
        return _make_record(TransitionOutcome.REFUSED, "UNDECLARED_TRANSITION")

    entry = registry[request.transition_id]
    gate_version = entry.get("gate_version", "")

    # 2. Authority check.
    required = Evidence[entry["required_authority"]]
    provided = Evidence[context.authority_basis]
    gate = AuthorityGate(required)
    decision = gate.check(provided)
    if decision is Decision.DENY:
        return _make_record(TransitionOutcome.REFUSED, "AUTHORITY_INVALID", gate_version)

    # 3 & 4. Risk class check.
    if request.risk_class in _HIGH_RISK:
        if not request.override_token:
            return _make_record(TransitionOutcome.REFUSED, "SUPERVISION_REQUIRED", gate_version)
        return _make_record(TransitionOutcome.SUPERVISED, "OVERRIDE_TOKEN_PRESENT", gate_version)

    # 5. Approved.
    return _make_record(TransitionOutcome.APPROVED, "APPROVED", gate_version)
