"""Tests proving evaluate() and evaluate_transition() have no divergent behaviour.

The gate decision (ALLOW/DENY) is performed by AuthorityGate in both paths.
This test suite confirms that for equivalent authority configurations, both
entrypoints produce the same outcome — satisfying the coherence requirement
from the PR #6 conflict-resolution review.
"""

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_gate import Evidence
from mgtp.evaluate import evaluate
from mgtp.evaluate_transition import evaluate_transition
from mgtp.types import (
    AuthorityContext,
    RiskClass,
    TransitionOutcome,
    TransitionRequest,
)

_TS = "2026-01-15T12:00:00Z"


def _req(
    transition_id="OP",
    risk_class=RiskClass.MEDIUM,
    irreversible=False,
    resource_identifier="res-x",
    trust_boundary_crossed=False,
    override_token=None,
    timestamp=_TS,
):
    return TransitionRequest(
        transition_id=transition_id,
        risk_class=risk_class,
        irreversible=irreversible,
        resource_identifier=resource_identifier,
        trust_boundary_crossed=trust_boundary_crossed,
        override_token=override_token,
        timestamp=timestamp,
    )


def _registry(transition_id="OP", required_authority="OWNER", risk_class="MEDIUM"):
    return {
        transition_id: {
            "id": transition_id,
            "irreversible": False,
            "risk_class": risk_class,
            "required_authority": required_authority,
            "gate_version": "v0.1",
        }
    }


def _eval_ctx(required_authority: str, actual_authority: str) -> AuthorityContext:
    """Context for evaluate(): authority_basis = required, provided_evidence = actual."""
    return AuthorityContext(
        actor_id="actor",
        authority_basis=required_authority,
        tenant_id="t1",
        provided_evidence=Evidence[actual_authority],
    )


def _trans_ctx(actual_authority: str) -> AuthorityContext:
    """Context for evaluate_transition(): authority_basis = actor's actual authority."""
    return AuthorityContext(
        actor_id="actor",
        authority_basis=actual_authority,
        tenant_id="t1",
    )


# ---------------------------------------------------------------------------
# Coherence: same gate decision for APPROVED cases
# ---------------------------------------------------------------------------


def test_approved_coherence_owner_required_owner_provided():
    req = _req()
    reg = _registry(required_authority="OWNER")
    eval_ctx = _eval_ctx("OWNER", "OWNER")
    trans_ctx = _trans_ctx("OWNER")

    r_eval = evaluate(req, eval_ctx)
    r_trans = evaluate_transition(req, trans_ctx, reg)

    assert r_eval.outcome is TransitionOutcome.APPROVED
    assert r_trans.outcome is TransitionOutcome.APPROVED


def test_approved_coherence_user_required_owner_provided():
    req = _req()
    reg = _registry(required_authority="USER")
    eval_ctx = _eval_ctx("USER", "OWNER")
    trans_ctx = _trans_ctx("OWNER")

    r_eval = evaluate(req, eval_ctx)
    r_trans = evaluate_transition(req, trans_ctx, reg)

    assert r_eval.outcome is TransitionOutcome.APPROVED
    assert r_trans.outcome is TransitionOutcome.APPROVED


def test_approved_coherence_none_required_user_provided():
    req = _req()
    reg = _registry(required_authority="NONE")
    eval_ctx = _eval_ctx("NONE", "USER")
    trans_ctx = _trans_ctx("USER")

    r_eval = evaluate(req, eval_ctx)
    r_trans = evaluate_transition(req, trans_ctx, reg)

    assert r_eval.outcome is TransitionOutcome.APPROVED
    assert r_trans.outcome is TransitionOutcome.APPROVED


# ---------------------------------------------------------------------------
# Coherence: same gate decision for REFUSED cases
# ---------------------------------------------------------------------------


def test_refused_coherence_owner_required_user_provided():
    req = _req()
    reg = _registry(required_authority="OWNER")
    eval_ctx = _eval_ctx("OWNER", "USER")
    trans_ctx = _trans_ctx("USER")

    r_eval = evaluate(req, eval_ctx)
    r_trans = evaluate_transition(req, trans_ctx, reg)

    assert r_eval.outcome is TransitionOutcome.REFUSED
    assert r_trans.outcome is TransitionOutcome.REFUSED


def test_refused_coherence_admin_required_owner_provided():
    req = _req()
    reg = _registry(required_authority="ADMIN")
    eval_ctx = _eval_ctx("ADMIN", "OWNER")
    trans_ctx = _trans_ctx("OWNER")

    r_eval = evaluate(req, eval_ctx)
    r_trans = evaluate_transition(req, trans_ctx, reg)

    assert r_eval.outcome is TransitionOutcome.REFUSED
    assert r_trans.outcome is TransitionOutcome.REFUSED


# ---------------------------------------------------------------------------
# Coherence: SUPERVISED path (CRITICAL + irreversible)
# ---------------------------------------------------------------------------


def test_supervised_coherence_critical_irreversible():
    req = _req(risk_class=RiskClass.CRITICAL, irreversible=True)
    reg = _registry(required_authority="ADMIN", risk_class="CRITICAL")
    eval_ctx = _eval_ctx("ADMIN", "ADMIN")
    trans_ctx = _trans_ctx("ADMIN")

    r_eval = evaluate(req, eval_ctx)
    r_trans = evaluate_transition(req, trans_ctx, reg)

    assert r_eval.outcome is TransitionOutcome.SUPERVISED
    assert r_trans.outcome is TransitionOutcome.SUPERVISED


# ---------------------------------------------------------------------------
# No third entrypoint — confirm only evaluate() and evaluate_transition() exist
# ---------------------------------------------------------------------------


def test_no_third_entrypoint_in_evaluate_module():
    """mgtp.evaluate exposes only 'evaluate' via __all__."""
    import mgtp.evaluate as mod

    assert mod.__all__ == ["evaluate"], (
        f"Unexpected extra entrypoints in mgtp.evaluate.__all__: {mod.__all__}"
    )


def test_no_third_entrypoint_in_evaluate_transition_module():
    """mgtp.evaluate_transition exposes only 'evaluate_transition' via __all__."""
    import mgtp.evaluate_transition as mod

    assert mod.__all__ == ["evaluate_transition"], (
        f"Unexpected extra entrypoints in mgtp.evaluate_transition.__all__: {mod.__all__}"
    )
