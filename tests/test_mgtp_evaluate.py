"""Tests for mgtp.evaluate — registry-free evaluator."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from authority_gate import Evidence
from mgtp.evaluate import evaluate
from mgtp.types import (
    AuthorityContext,
    DecisionRecord,
    RiskClass,
    TransitionOutcome,
    TransitionRequest,
)

_TS = "2026-01-01T00:00:00Z"


def _req(
    transition_id="tx-001",
    risk_class=RiskClass.MEDIUM,
    irreversible=False,
    resource_identifier="res://alpha",
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


def _ctx(authority_basis="OWNER", provided_evidence=Evidence.OWNER, actor_id="alice", tenant_id="t1"):
    return AuthorityContext(
        actor_id=actor_id,
        authority_basis=authority_basis,
        tenant_id=tenant_id,
        provided_evidence=provided_evidence,
    )


# ---------------------------------------------------------------------------
# Happy path — APPROVED
# ---------------------------------------------------------------------------


def test_approved_when_authority_sufficient():
    rec = evaluate(_req(), _ctx())
    assert rec.outcome == TransitionOutcome.APPROVED
    assert rec.reason == "authority_sufficient"
    assert rec.transition_id == "tx-001"


def test_approved_returns_decision_record():
    rec = evaluate(_req(), _ctx())
    assert isinstance(rec, DecisionRecord)


# ---------------------------------------------------------------------------
# REFUSED paths
# ---------------------------------------------------------------------------


def test_refused_when_authority_insufficient():
    ctx = _ctx(authority_basis="OWNER", provided_evidence=Evidence.USER)
    rec = evaluate(_req(), ctx)
    assert rec.outcome == TransitionOutcome.REFUSED
    assert rec.reason == "authority_insufficient"


def test_refused_when_provided_none_evidence():
    ctx = _ctx(authority_basis="OWNER", provided_evidence=Evidence.NONE)
    rec = evaluate(_req(), ctx)
    assert rec.outcome == TransitionOutcome.REFUSED


# ---------------------------------------------------------------------------
# SUPERVISED path
# ---------------------------------------------------------------------------


def test_supervised_for_critical_irreversible():
    req = _req(risk_class=RiskClass.CRITICAL, irreversible=True)
    ctx = _ctx(authority_basis="ADMIN", provided_evidence=Evidence.ADMIN)
    rec = evaluate(req, ctx)
    assert rec.outcome == TransitionOutcome.SUPERVISED
    assert rec.reason == "critical_irreversible_supervised"


def test_not_supervised_when_critical_but_reversible():
    req = _req(risk_class=RiskClass.CRITICAL, irreversible=False)
    ctx = _ctx(authority_basis="ADMIN", provided_evidence=Evidence.ADMIN)
    rec = evaluate(req, ctx)
    assert rec.outcome == TransitionOutcome.APPROVED


def test_not_supervised_when_irreversible_but_not_critical():
    req = _req(risk_class=RiskClass.HIGH, irreversible=True)
    ctx = _ctx(authority_basis="OWNER", provided_evidence=Evidence.OWNER)
    rec = evaluate(req, ctx)
    assert rec.outcome == TransitionOutcome.APPROVED


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_raises_value_error_when_provided_evidence_none():
    ctx = AuthorityContext(actor_id="alice", authority_basis="OWNER", tenant_id="t1")
    with pytest.raises(ValueError, match="provided_evidence is required"):
        evaluate(_req(), ctx)


def test_raises_value_error_on_unknown_authority_basis():
    ctx = _ctx(authority_basis="UNKNOWN_LEVEL")
    with pytest.raises(ValueError, match="Unknown authority_basis"):
        evaluate(_req(), ctx)


# ---------------------------------------------------------------------------
# Record fields
# ---------------------------------------------------------------------------


def test_authority_basis_reflects_required_level():
    ctx = _ctx(authority_basis="OWNER")
    rec = evaluate(_req(), ctx)
    assert rec.authority_basis == "OWNER"


def test_risk_class_propagated():
    rec = evaluate(_req(risk_class=RiskClass.HIGH), _ctx())
    assert rec.risk_class == RiskClass.HIGH


def test_record_is_frozen():
    rec = evaluate(_req(), _ctx())
    try:
        rec.outcome = TransitionOutcome.REFUSED  # type: ignore[misc]
        assert False, "Should raise"
    except (AttributeError, TypeError):
        pass


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_deterministic_same_inputs():
    r1 = evaluate(_req(), _ctx())
    r2 = evaluate(_req(), _ctx())
    assert r1 == r2
    assert r1.canonical_bytes == r2.canonical_bytes


def test_canonical_bytes_deterministic_across_20_calls():
    results = [evaluate(_req(), _ctx()).canonical_bytes for _ in range(20)]
    assert all(r == results[0] for r in results)


# ---------------------------------------------------------------------------
# Boundary: importing mgtp does not affect authority_gate behaviour
# ---------------------------------------------------------------------------


def test_authority_gate_unaffected_after_mgtp_import():
    from authority_gate import AuthorityGate, Decision

    import mgtp  # noqa: F401

    gate = AuthorityGate(Evidence.OWNER)
    assert gate.check(Evidence.ADMIN) is Decision.ALLOW
    assert gate.check(Evidence.USER) is Decision.DENY


def test_commit_gate_not_imported_by_mgtp():
    import importlib

    mgtp_keys = [k for k in sys.modules if k == "mgtp" or k.startswith("mgtp.")]
    saved = {k: sys.modules.pop(k) for k in mgtp_keys}
    pre = {k for k in sys.modules if k.startswith("commit_gate")}
    try:
        importlib.import_module("mgtp")
        post = {k for k in sys.modules if k.startswith("commit_gate")}
        assert not (post - pre), f"mgtp import introduced commit_gate modules: {post - pre}"
    finally:
        for k in [k for k in sys.modules if k == "mgtp" or k.startswith("mgtp.")]:
            sys.modules.pop(k, None)
        sys.modules.update(saved)
