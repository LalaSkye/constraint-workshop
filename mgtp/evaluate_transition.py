"""mgtp.evaluate_transition — Registry-based MGTP evaluator.

Public entrypoint: evaluate_transition()

This function is a thin wrapper around evaluate() (mgtp.evaluate).  It adds
registry pre-check and context mapping, then delegates the core gate decision
to evaluate().  There is no divergent gate behaviour between the two paths.

Evaluation pipeline:
  1. Registry membership check → REFUSED / transition_not_registered
  2. Map (entry["required_authority"], context.authority_basis) to an
     (authority_basis=required, provided_evidence=actual) context.
  3. Delegate to evaluate() for the gate decision.
  4. Reconstruct DecisionRecord with the actor's original authority_basis and
     extended audit fields (context_hash, actor_id, tenant_id, …).

Invariants:
- evaluate_transition() is pure: same inputs produce same output.
- No file I/O.  No network calls.  No state mutation.
- No randomness.  No clock calls.  No logging.
"""

import hashlib
import json

from authority_gate import Evidence

__all__ = ["evaluate_transition"]

from .decision_record import DecisionRecord
from .evaluate import evaluate
from .types import AuthorityContext, TransitionOutcome, TransitionRequest


def _context_hash(request: TransitionRequest, context: AuthorityContext) -> str:
    """Deterministic sha256 over the canonical representation of (request, context)."""
    payload = {
        "actor_id": context.actor_id,
        "authority_basis": context.authority_basis,
        "irreversible": request.irreversible,
        "override_token": request.override_token,
        "resource_identifier": request.resource_identifier,
        "risk_class": request.risk_class.value,
        "tenant_id": context.tenant_id,
        "timestamp": request.timestamp,
        "transition_id": request.transition_id,
        "trust_boundary_crossed": request.trust_boundary_crossed,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def evaluate_transition(
    request: TransitionRequest,
    context: AuthorityContext,
    registry: dict,
) -> DecisionRecord:
    """Evaluate a TransitionRequest against the registry and authority context.

    This is a thin wrapper around evaluate(): registry lookup and context
    mapping happen here; the core gate decision is delegated to evaluate().

    Args:
        request:  The transition being requested.
        context:  The authority context of the requesting actor.
                  ``context.authority_basis`` names the *provided* Evidence
                  level (looked up in the Evidence enum).
        registry: Mapping of transition_id -> entry dict.  Each entry must
                  have a ``required_authority`` key whose value is a valid
                  Evidence member name.

    Returns:
        A DecisionRecord with outcome APPROVED, REFUSED, or SUPERVISED.
    """
    ctx_hash = _context_hash(request, context)

    # 1. Registry membership check.
    if request.transition_id not in registry:
        return DecisionRecord(
            transition_id=request.transition_id,
            outcome=TransitionOutcome.REFUSED,
            authority_basis=context.authority_basis,
            risk_class=request.risk_class,
            reason="transition_not_registered",
            actor_id=context.actor_id,
            tenant_id=context.tenant_id,
            timestamp=request.timestamp,
            context_hash=ctx_hash,
        )

    entry = registry[request.transition_id]
    gate_version = entry.get("gate_version", "")

    # 2. Map to evaluate() context:
    #    authority_basis    = required level (from registry)
    #    provided_evidence  = actual evidence (from context.authority_basis)
    eval_context = AuthorityContext(
        actor_id=context.actor_id,
        authority_basis=entry["required_authority"],
        tenant_id=context.tenant_id,
        provided_evidence=Evidence[context.authority_basis],
    )

    # 3. Delegate to evaluate() for the gate decision.
    gate_result = evaluate(request, eval_context)

    # 4. Reconstruct with the actor's original authority_basis and audit fields.
    return DecisionRecord(
        transition_id=gate_result.transition_id,
        outcome=gate_result.outcome,
        authority_basis=context.authority_basis,
        risk_class=gate_result.risk_class,
        reason=gate_result.reason,
        actor_id=context.actor_id,
        tenant_id=context.tenant_id,
        timestamp=request.timestamp,
        gate_version=gate_version,
        context_hash=ctx_hash,
    )
