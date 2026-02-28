"""MGTP evaluation: deterministic transition-approval logic."""

from authority_gate import AuthorityGate, Decision, Evidence

from .types import (
    AuthorityContext,
    DecisionRecord,
    RiskClass,
    TransitionOutcome,
    TransitionRequest,
)


def evaluate(request: TransitionRequest, context: AuthorityContext) -> DecisionRecord:
    """Evaluate a TransitionRequest against an AuthorityContext.

    Raises ValueError if context.provided_evidence is None.
    Raises ValueError if context.authority_basis does not map to a known Evidence level.
    """
    if context.provided_evidence is None:
        raise ValueError("provided_evidence is required for MGTP evaluation")

    try:
        required = Evidence[context.authority_basis]
    except KeyError:
        raise ValueError(f"Unknown authority_basis: {context.authority_basis!r}")

    gate = AuthorityGate(required)
    decision = gate.check(context.provided_evidence)

    if decision == Decision.DENY:
        outcome = TransitionOutcome.REFUSED
    elif request.irreversible and request.risk_class == RiskClass.CRITICAL:
        outcome = TransitionOutcome.SUPERVISED
    else:
        outcome = TransitionOutcome.APPROVED

    return DecisionRecord(
        transition_id=request.transition_id,
        outcome=outcome,
        risk_class=request.risk_class,
        actor_id=context.actor_id,
        authority_basis=context.authority_basis,
        timestamp=request.timestamp,
    )
