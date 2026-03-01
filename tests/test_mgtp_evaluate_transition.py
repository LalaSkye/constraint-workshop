"""Tests for mgtp.evaluate_transition — registry-based thin-wrapper evaluator."""

import os
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mgtp.evaluate_transition import evaluate_transition
from mgtp.registry import load_registry
from mgtp.types import AuthorityContext, DecisionRecord, RiskClass, TransitionOutcome, TransitionRequest

_REAL_REGISTRY = os.path.join(
    os.path.dirname(__file__), "..", "registry", "TRANSITION_REGISTRY_v0.2.yaml"
)
_TS = "2025-06-01T12:00:00Z"


@pytest.fixture()
def real_registry():
    return load_registry(_REAL_REGISTRY)


def _req(
    transition_id="TOOL_CALL_HTTP",
    risk_class=RiskClass.HIGH,
    irreversible=True,
    override_token=None,
    resource_identifier="res-1",
    trust_boundary_crossed=False,
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


def _ctx(actor_id="alice", authority_basis="OWNER", tenant_id="t1"):
    return AuthorityContext(actor_id=actor_id, authority_basis=authority_basis, tenant_id=tenant_id)


# ---------------------------------------------------------------------------
# Scenario 1: undeclared transition → REFUSED
# ---------------------------------------------------------------------------


def test_undeclared_transition_refused(real_registry):
    req = _req(transition_id="NO_SUCH_TRANSITION")
    rec = evaluate_transition(req, _ctx(), real_registry)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "transition_not_registered"


# ---------------------------------------------------------------------------
# Scenario 2: insufficient authority → REFUSED
# ---------------------------------------------------------------------------


def test_insufficient_authority_refused(real_registry):
    req = _req()
    ctx = _ctx(authority_basis="USER")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "authority_insufficient"


def test_none_authority_refused(real_registry):
    req = _req()
    ctx = _ctx(authority_basis="NONE")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "authority_insufficient"


# ---------------------------------------------------------------------------
# Scenario 3: sufficient authority → APPROVED (HIGH risk, not CRITICAL+irreversible)
# ---------------------------------------------------------------------------


def test_owner_approved_for_high_risk(real_registry):
    req = _req(risk_class=RiskClass.HIGH, irreversible=False)
    ctx = _ctx(authority_basis="OWNER")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.outcome is TransitionOutcome.APPROVED
    assert rec.reason_code == "authority_sufficient"


# ---------------------------------------------------------------------------
# Scenario 4: CRITICAL + irreversible → SUPERVISED
# ---------------------------------------------------------------------------


def test_critical_irreversible_supervised(tmp_path):
    content = textwrap.dedent("""
        version: 0.2
        transitions:
          - id: CRITICAL_OP
            irreversible: true
            risk_class: CRITICAL
            required_authority: ADMIN
            gate_version: v0.2
    """)
    p = tmp_path / "r.yaml"
    p.write_text(content)
    reg = load_registry(str(p))

    req = _req(transition_id="CRITICAL_OP", risk_class=RiskClass.CRITICAL, irreversible=True)
    ctx = _ctx(authority_basis="ADMIN")
    rec = evaluate_transition(req, ctx, reg)
    assert rec.outcome is TransitionOutcome.SUPERVISED
    assert rec.reason_code == "critical_irreversible_supervised"


# ---------------------------------------------------------------------------
# Scenario 5: LOW risk with sufficient authority → APPROVED
# ---------------------------------------------------------------------------


def test_low_risk_approved(tmp_path):
    content = textwrap.dedent("""
        version: 0.2
        transitions:
          - id: READ_ONLY
            irreversible: false
            risk_class: LOW
            required_authority: USER
            gate_version: v0.1
    """)
    p = tmp_path / "r.yaml"
    p.write_text(content)
    reg = load_registry(str(p))

    req = _req(transition_id="READ_ONLY", risk_class=RiskClass.LOW, irreversible=False)
    ctx = _ctx(authority_basis="USER")
    rec = evaluate_transition(req, ctx, reg)
    assert rec.outcome is TransitionOutcome.APPROVED
    assert rec.reason_code == "authority_sufficient"


# ---------------------------------------------------------------------------
# Result is a DecisionRecord
# ---------------------------------------------------------------------------


def test_returns_decision_record(real_registry):
    req = _req(risk_class=RiskClass.HIGH, irreversible=False)
    rec = evaluate_transition(req, _ctx(), real_registry)
    assert isinstance(rec, DecisionRecord)


# ---------------------------------------------------------------------------
# Audit fields populated
# ---------------------------------------------------------------------------


def test_audit_fields_populated(real_registry):
    req = _req(risk_class=RiskClass.HIGH, irreversible=False)
    ctx = _ctx(actor_id="alice", tenant_id="t1")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.actor_id == "alice"
    assert rec.tenant_id == "t1"
    assert rec.timestamp == _TS
    assert rec.gate_version == "v0.2"
    assert rec.context_hash != ""
    assert rec.decision_id != ""
    assert rec.content_hash != ""


def test_authority_basis_is_actor_authority(real_registry):
    """authority_basis in the record reflects the actor's provided authority, not required."""
    req = _req(risk_class=RiskClass.HIGH, irreversible=False)
    rec = evaluate_transition(req, _ctx(authority_basis="OWNER"), real_registry)
    assert rec.authority_basis == "OWNER"


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_deterministic_same_inputs(real_registry):
    req = _req(risk_class=RiskClass.HIGH, irreversible=False)
    ctx = _ctx()
    r1 = evaluate_transition(req, ctx, real_registry)
    r2 = evaluate_transition(req, ctx, real_registry)
    assert r1.canonical_bytes == r2.canonical_bytes
    assert r1.content_hash == r2.content_hash
    assert r1.decision_id == r2.decision_id
