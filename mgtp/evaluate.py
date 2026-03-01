"""mgtp.evaluate — Canonical registry-free MGTP evaluator.

Public entrypoint: evaluate()

This module exposes exactly one evaluation function.  For registry-based
evaluation see mgtp.evaluate_transition.

Invariants:
- evaluate() is pure: same inputs produce same output.
- No file I/O.  No network calls.  No state mutation.
- No randomness.  No clock calls.  No logging.
"""

from authority_gate import AuthorityGate, Decision, Evidence

__all__ = ["evaluate"]

from .types import AuthorityContext, DecisionRecord, RiskClass, TransitionOutcome, TransitionRequest


def evaluate(request: TransitionRequest, context: AuthorityContext) -> DecisionRecord:
    """Evaluate a TransitionRequest against an AuthorityContext without a registry.

    ``context.authority_basis`` names the *required* Evidence level.
    ``context.provided_evidence`` carries the *actual* Evidence provided.

    Raises:
        ValueError: if ``context.provided_evidence`` is None.
        ValueError: if ``context.authority_basis`` is not a recognised Evidence name.

    Returns:
        A DecisionRecord with outcome APPROVED, REFUSED, or SUPERVISED.
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
