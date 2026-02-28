"""MGTP enforcement-grade verification tests.

T1: Golden determinism fixture — byte-for-byte and hash equality.
T2: Cross-run stability — 100-iteration loop.
T3: Fail-closed guard — missing evidence, out-of-window decision_time.
T4: Surface area integrity — no runtime mutation of authority modules.
"""

import base64
import hashlib
import importlib
import sys
import types

import pytest

from authority_gate import AuthorityGate, Decision, Evidence
from mgtp.evaluator import evaluate
from mgtp.types import (
    AuthorityContext,
    DecisionRecord,
    RiskClass,
    TransitionOutcome,
    TransitionRequest,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

GOLDEN_RECORD = DecisionRecord(
    transition_id="txn-golden-001",
    verdict=TransitionOutcome.APPROVED,
    reasons=("evidence_sufficient",),
    decision_time="2026-01-01T00:00:00Z",
    authority_basis="OWNER",
)

# Pre-computed golden values (generated once; must never change).
GOLDEN_CANONICAL_B64 = (
    "eyJhdXRob3JpdHlfYmFzaXMiOiJPV05FUiIsImRlY2lzaW9uX3RpbWUiOiIyMDI2LTAx"
    "LTAxVDAwOjAwOjAwWiIsInJlYXNvbnMiOlsiZXZpZGVuY2Vfc3VmZmljaWVudCJdLCJ0"
    "cmFuc2l0aW9uX2lkIjoidHhuLWdvbGRlbi0wMDEiLCJ2ZXJkaWN0IjoiQVBQUk9WRUQi"
    "fQ=="
)
GOLDEN_DECISION_HASH = "3f55453de918d9228eb4e1eda60f9d2e4555834f2ffc2e70b1e5ff6d0bb9a254"

# ---------------------------------------------------------------------------
# T1: Golden determinism fixture
# ---------------------------------------------------------------------------


def test_t1_golden_canonical_bytes_exact():
    """canonical_bytes() must match pre-computed golden value byte-for-byte."""
    expected = base64.b64decode(GOLDEN_CANONICAL_B64)
    assert GOLDEN_RECORD.canonical_bytes() == expected


def test_t1_golden_decision_hash_exact():
    """decision_hash must match pre-computed golden SHA-256 hex digest."""
    assert GOLDEN_RECORD.decision_hash == GOLDEN_DECISION_HASH


def test_t1_golden_hash_is_sha256_of_canonical_bytes():
    """decision_hash is always sha256(canonical_bytes())."""
    cb = GOLDEN_RECORD.canonical_bytes()
    assert hashlib.sha256(cb).hexdigest() == GOLDEN_RECORD.decision_hash


# ---------------------------------------------------------------------------
# T2: Cross-run stability — 100-iteration loop
# ---------------------------------------------------------------------------


def test_t2_canonical_bytes_stable_100_iterations():
    """canonical_bytes() returns identical bytes across 100 consecutive calls."""
    first = GOLDEN_RECORD.canonical_bytes()
    for _ in range(99):
        assert GOLDEN_RECORD.canonical_bytes() == first, "canonical_bytes() not stable"


def test_t2_decision_hash_stable_100_iterations():
    """decision_hash returns identical digest across 100 consecutive calls."""
    first = GOLDEN_RECORD.decision_hash
    for _ in range(99):
        assert GOLDEN_RECORD.decision_hash == first, "decision_hash not stable"


# ---------------------------------------------------------------------------
# T3: Fail-closed guard tests
# ---------------------------------------------------------------------------

_SAFE_REQUEST = TransitionRequest(
    transition_id="txn-test-001",
    risk_class=RiskClass.LOW,
    irreversible=False,
    resource_identifier="res-001",
    trust_boundary_crossed=False,
    override_token=None,
    timestamp="2026-01-01T00:00:00Z",
)

_SAFE_CONTEXT = AuthorityContext(
    actor_id="actor-001",
    authority_basis="OWNER",
    tenant_id="tenant-001",
)

_DECISION_TIME_IN_WINDOW = "2026-01-01T00:30:00Z"  # 30 min after request — within 1h window
_DECISION_TIME_OUT_OF_WINDOW = "2026-01-01T02:00:00Z"  # 2 hours after — outside 1h window


def test_t3_allow_verdict_with_none_evidence_refuses():
    """If provided_evidence is None, evaluation must REFUSE regardless of gate."""
    record = evaluate(
        request=_SAFE_REQUEST,
        context=_SAFE_CONTEXT,
        provided_evidence=None,
        decision_time=_DECISION_TIME_IN_WINDOW,
    )
    assert record.verdict is TransitionOutcome.REFUSED
    assert "missing_evidence" in record.reasons


def test_t3_none_evidence_reason_code_is_missing_evidence():
    """Reason code for missing evidence must be 'missing_evidence'."""
    record = evaluate(
        request=_SAFE_REQUEST,
        context=_SAFE_CONTEXT,
        provided_evidence=None,
        decision_time=_DECISION_TIME_IN_WINDOW,
    )
    assert record.reasons == ("missing_evidence",)


def test_t3_decision_time_outside_window_refuses():
    """decision_time outside authority window must produce REFUSED."""
    record = evaluate(
        request=_SAFE_REQUEST,
        context=_SAFE_CONTEXT,
        provided_evidence=Evidence.OWNER,
        decision_time=_DECISION_TIME_OUT_OF_WINDOW,
    )
    assert record.verdict is TransitionOutcome.REFUSED
    assert "decision_time_outside_authority_window" in record.reasons


def test_t3_decision_time_outside_window_reason_code():
    """Reason code for out-of-window must be 'decision_time_outside_authority_window'."""
    record = evaluate(
        request=_SAFE_REQUEST,
        context=_SAFE_CONTEXT,
        provided_evidence=Evidence.OWNER,
        decision_time=_DECISION_TIME_OUT_OF_WINDOW,
    )
    assert record.reasons == ("decision_time_outside_authority_window",)


def test_t3_decision_time_before_request_refuses():
    """decision_time before request.timestamp must REFUSE (fail-closed)."""
    record = evaluate(
        request=_SAFE_REQUEST,
        context=_SAFE_CONTEXT,
        provided_evidence=Evidence.OWNER,
        decision_time="2025-12-31T23:59:59Z",  # before request timestamp
    )
    assert record.verdict is TransitionOutcome.REFUSED
    assert "decision_time_outside_authority_window" in record.reasons


def test_t3_insufficient_evidence_refuses():
    """Evidence below required level must REFUSE."""
    record = evaluate(
        request=_SAFE_REQUEST,
        context=_SAFE_CONTEXT,
        provided_evidence=Evidence.USER,  # OWNER gate requires OWNER+
        decision_time=_DECISION_TIME_IN_WINDOW,
    )
    assert record.verdict is TransitionOutcome.REFUSED
    assert "insufficient_evidence" in record.reasons


def test_t3_sufficient_evidence_approves():
    """Sufficient evidence within window must produce APPROVED for safe request."""
    record = evaluate(
        request=_SAFE_REQUEST,
        context=_SAFE_CONTEXT,
        provided_evidence=Evidence.OWNER,
        decision_time=_DECISION_TIME_IN_WINDOW,
    )
    assert record.verdict is TransitionOutcome.APPROVED


def test_t3_irreversible_request_supervised():
    """Irreversible request with sufficient evidence must be SUPERVISED (not APPROVED)."""
    irreversible_req = TransitionRequest(
        transition_id="txn-irrev-001",
        risk_class=RiskClass.HIGH,
        irreversible=True,
        resource_identifier="res-001",
        trust_boundary_crossed=False,
        override_token=None,
        timestamp="2026-01-01T00:00:00Z",
    )
    record = evaluate(
        request=irreversible_req,
        context=_SAFE_CONTEXT,
        provided_evidence=Evidence.ADMIN,
        decision_time=_DECISION_TIME_IN_WINDOW,
    )
    assert record.verdict is TransitionOutcome.SUPERVISED
    assert "irreversible_or_trust_boundary" in record.reasons


# ---------------------------------------------------------------------------
# T4: Surface area integrity — no runtime mutation of authority modules
# ---------------------------------------------------------------------------


def test_t4_authority_gate_module_not_mutated():
    """authority_gate module attributes must not be modified at runtime."""
    import authority_gate as ag

    original_evidence_members = {e.name: e.value for e in ag.Evidence}
    original_decision_members = {d.name: d.value for d in ag.Decision}

    # Import MGTP evaluator (which consumes authority_gate)
    import mgtp.evaluator  # noqa: F401

    # Verify Evidence and Decision enums are intact
    assert {e.name: e.value for e in ag.Evidence} == original_evidence_members
    assert {d.name: d.value for d in ag.Decision} == original_decision_members
    assert ag.AuthorityGate is AuthorityGate


def test_t4_mgtp_does_not_redefine_evidence():
    """mgtp package must not define its own Evidence or Decision classes.

    Importing from authority_gate (consuming) is allowed; defining a
    parallel implementation inside mgtp is not.
    """
    import authority_gate as ag
    import mgtp.evaluator
    import mgtp.types

    # authority_gate is the canonical source; mgtp may import but not replace
    assert mgtp.types.__dict__.get("Evidence") is None, "mgtp.types must not define Evidence"
    assert mgtp.types.__dict__.get("Decision") is None, "mgtp.types must not define Decision"
    assert mgtp.types.__dict__.get("AuthorityGate") is None, "mgtp.types must not define AuthorityGate"

    # If mgtp.evaluator re-exports Evidence it must be the *same* object
    ev = mgtp.evaluator.__dict__.get("Evidence")
    if ev is not None:
        assert ev is ag.Evidence, "mgtp.evaluator.Evidence must be authority_gate.Evidence"
    dec = mgtp.evaluator.__dict__.get("Decision")
    if dec is not None:
        assert dec is ag.Decision, "mgtp.evaluator.Decision must be authority_gate.Decision"
    gate = mgtp.evaluator.__dict__.get("AuthorityGate")
    if gate is not None:
        assert gate is ag.AuthorityGate, "mgtp.evaluator.AuthorityGate must be authority_gate.AuthorityGate"


def test_t4_authority_gate_class_is_unchanged():
    """AuthorityGate class dict must not gain new attributes after mgtp import."""
    import authority_gate as ag

    before = set(vars(ag.AuthorityGate).keys())

    import mgtp.evaluator  # noqa: F401

    after = set(vars(ag.AuthorityGate).keys())
    assert before == after, f"AuthorityGate gained attributes: {after - before}"


def test_t4_stop_machine_module_not_mutated():
    """stop_machine module must not be mutated by importing mgtp."""
    import stop_machine as sm

    original_state_members = {s.name for s in sm.State}
    original_attrs = set(vars(sm).keys())

    import mgtp.evaluator  # noqa: F401

    assert {s.name for s in sm.State} == original_state_members
    assert set(vars(sm).keys()) == original_attrs
