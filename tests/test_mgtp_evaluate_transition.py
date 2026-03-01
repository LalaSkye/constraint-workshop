"""Tests for mgtp.evaluate_transition — decision scenarios."""

import os
import textwrap

import pytest

from mgtp.evaluate_transition import evaluate_transition
from mgtp.registry import load_registry
from mgtp.types import AuthorityContext, RiskClass, TransitionOutcome, TransitionRequest

_REAL_REGISTRY = os.path.join(
    os.path.dirname(__file__), "..", "registry", "TRANSITION_REGISTRY_v0.2.yaml"
)

_TS = "2025-06-01T12:00:00Z"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
    return AuthorityContext(
        actor_id=actor_id,
        authority_basis=authority_basis,
        tenant_id=tenant_id,
    )


# ---------------------------------------------------------------------------
# Scenario 1: undeclared transition
# ---------------------------------------------------------------------------

def test_undeclared_transition_refused(real_registry):
    req = _req(transition_id="NO_SUCH_TRANSITION")
    rec = evaluate_transition(req, _ctx(), real_registry)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "UNDECLARED_TRANSITION"


# ---------------------------------------------------------------------------
# Scenario 2: insufficient authority
# ---------------------------------------------------------------------------

def test_insufficient_authority_refused(real_registry):
    # TOOL_CALL_HTTP requires OWNER; USER is insufficient
    req = _req()
    ctx = _ctx(authority_basis="USER")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "AUTHORITY_INVALID"


def test_none_authority_refused(real_registry):
    req = _req()
    ctx = _ctx(authority_basis="NONE")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "AUTHORITY_INVALID"


# ---------------------------------------------------------------------------
# Scenario 3: HIGH risk without override -> SUPERVISION_REQUIRED
# ---------------------------------------------------------------------------

def test_high_risk_no_override_refused(real_registry):
    req = _req(risk_class=RiskClass.HIGH, override_token=None)
    ctx = _ctx(authority_basis="OWNER")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "SUPERVISION_REQUIRED"


def test_critical_risk_no_override_refused(real_registry, tmp_path):
    # Add a CRITICAL entry to a temporary registry
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

    req = _req(transition_id="CRITICAL_OP", risk_class=RiskClass.CRITICAL, override_token=None)
    ctx = _ctx(authority_basis="ADMIN")
    rec = evaluate_transition(req, ctx, reg)
    assert rec.outcome is TransitionOutcome.REFUSED
    assert rec.reason_code == "SUPERVISION_REQUIRED"


# ---------------------------------------------------------------------------
# Scenario 4: HIGH risk WITH override -> SUPERVISED
# ---------------------------------------------------------------------------

def test_high_risk_with_override_supervised(real_registry):
    req = _req(risk_class=RiskClass.HIGH, override_token="tok-xyz")
    ctx = _ctx(authority_basis="OWNER")
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.outcome is TransitionOutcome.SUPERVISED
    assert rec.reason_code == "OVERRIDE_TOKEN_PRESENT"


# ---------------------------------------------------------------------------
# Scenario 5: LOW/MEDIUM risk with sufficient authority -> APPROVED
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

    req = _req(transition_id="READ_ONLY", risk_class=RiskClass.LOW, override_token=None)
    ctx = _ctx(authority_basis="USER")
    rec = evaluate_transition(req, ctx, reg)
    assert rec.outcome is TransitionOutcome.APPROVED
    assert rec.reason_code == "APPROVED"


# ---------------------------------------------------------------------------
# Determinism: identical inputs produce identical records
# ---------------------------------------------------------------------------

def test_deterministic_same_inputs(real_registry):
    req = _req(override_token="tok-abc")
    ctx = _ctx()
    rec1 = evaluate_transition(req, ctx, real_registry)
    rec2 = evaluate_transition(req, ctx, real_registry)
    assert rec1.canonical_bytes == rec2.canonical_bytes
    assert rec1.content_hash == rec2.content_hash
    assert rec1.decision_id == rec2.decision_id


# ---------------------------------------------------------------------------
# Record fields populated correctly
# ---------------------------------------------------------------------------

def test_record_fields_populated(real_registry):
    req = _req(override_token="tok-abc")
    ctx = _ctx()
    rec = evaluate_transition(req, ctx, real_registry)
    assert rec.transition_id == "TOOL_CALL_HTTP"
    assert rec.actor_id == "alice"
    assert rec.tenant_id == "t1"
    assert rec.authority_basis == "OWNER"
    assert rec.timestamp == _TS
    assert rec.gate_version == "v0.2"
    assert rec.context_hash != ""
    assert rec.decision_id != ""
    assert rec.content_hash != ""
