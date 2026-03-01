"""mgtp.evaluate — Pure transition evaluator.

Invariants:
- evaluate_transition is pure: same inputs produce same output.
- No file I/O. No network calls. No state mutation.
- No randomness. No clock calls. No logging.
"""

from authority_gate import AuthorityGate, Decision, Evidence

from .types import AuthorityContext, DecisionRecord, RiskClass, TransitionOutcome, TransitionRequest


def evaluate_transition(
    request: TransitionRequest,
    context: AuthorityContext,
    registry: dict,
) -> DecisionRecord:
    """Evaluate whether a transition is permitted.

    Args:
        request:  The transition being requested.
        context:  The authority context of the requesting actor.
        registry: Mapping of transition_id -> transition definition dict.
                  Each definition must have a ``required_authority`` key
                  whose value is a valid ``Evidence`` member name.

    Returns:
        A ``DecisionRecord`` with outcome APPROVED or REFUSED.
    """
    entry = registry.get(request.transition_id)

    if entry is None:
        return DecisionRecord(
            transition_id=request.transition_id,
            outcome=TransitionOutcome.REFUSED,
            authority_basis=context.authority_basis,
            risk_class=request.risk_class,
            reason="transition_not_registered",
        )

    required = Evidence[entry["required_authority"]]
    provided = Evidence[context.authority_basis]
    gate = AuthorityGate(required)
    decision = gate.check(provided)

    if decision == Decision.DENY:
        return DecisionRecord(
            transition_id=request.transition_id,
            outcome=TransitionOutcome.REFUSED,
            authority_basis=context.authority_basis,
            risk_class=request.risk_class,
            reason="authority_insufficient",
        )

    return DecisionRecord(
        transition_id=request.transition_id,
        outcome=TransitionOutcome.APPROVED,
        authority_basis=context.authority_basis,
        risk_class=request.risk_class,
        reason="authority_sufficient",
    )


def evaluate(request: TransitionRequest, context: AuthorityContext) -> DecisionRecord:
    """Evaluate a TransitionRequest against an AuthorityContext without a registry.

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
        reason = "authority_insufficient"
        outcome = TransitionOutcome.REFUSED
    elif request.irreversible and request.risk_class == RiskClass.CRITICAL:
        reason = "critical_irreversible_supervised"
        outcome = TransitionOutcome.SUPERVISED
    else:
        reason = "authority_sufficient"
        outcome = TransitionOutcome.APPROVED

    return DecisionRecord(
        transition_id=request.transition_id,
        outcome=outcome,
        authority_basis=context.authority_basis,
        risk_class=request.risk_class,
        reason=reason,
    )
