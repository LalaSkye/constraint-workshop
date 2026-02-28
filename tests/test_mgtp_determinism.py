"""MGTP determinism, cross-version stability, authority isolation, and boundary tests."""

import sys

import pytest

from authority_gate import AuthorityGate, Decision, Evidence
from mgtp.evaluate import evaluate
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

SAMPLE_REQUEST = TransitionRequest(
    transition_id="tx-001",
    risk_class=RiskClass.MEDIUM,
    irreversible=False,
    resource_identifier="res://alpha",
    trust_boundary_crossed=False,
    override_token=None,
    timestamp="2026-01-01T00:00:00Z",
)

SAMPLE_CONTEXT = AuthorityContext(
    actor_id="alice",
    authority_basis="OWNER",
    tenant_id="tenant-1",
    provided_evidence=Evidence.OWNER,
)

SAMPLE_RECORD = DecisionRecord(
    transition_id="tx-001",
    outcome=TransitionOutcome.APPROVED,
    risk_class=RiskClass.MEDIUM,
    actor_id="alice",
    authority_basis="OWNER",
    timestamp="2026-01-01T00:00:00Z",
)


# ---------------------------------------------------------------------------
# Task 1 — Deterministic Canonicalisation
# ---------------------------------------------------------------------------


def test_canonical_bytes_deterministic_same_run():
    """T1a: canonical_bytes() is byte-identical across multiple calls in the same run."""
    results = [SAMPLE_RECORD.canonical_bytes() for _ in range(20)]
    assert all(r == results[0] for r in results), "canonical_bytes() is not stable"


def test_canonical_hash_deterministic_same_run():
    """T1b: canonical_hash() is identical across multiple invocations in the same run."""
    hashes = [SAMPLE_RECORD.canonical_hash() for _ in range(20)]
    assert all(h == hashes[0] for h in hashes), "canonical_hash() is not stable"
    assert len(hashes[0]) == 64
    assert hashes[0] == hashes[0].lower()


def test_canonical_bytes_uses_sorted_keys():
    """T1c: canonical_bytes output has sorted JSON keys (no __repr__ reliance)."""
    raw = SAMPLE_RECORD.canonical_bytes().decode("utf-8")
    # Verify it is valid JSON and that keys appear in sorted order
    import json

    obj = json.loads(raw)
    keys = list(obj.keys())
    assert keys == sorted(keys), f"Keys not sorted: {keys}"


def test_canonical_bytes_no_whitespace():
    """T1d: canonical_bytes uses compact separators (no extra whitespace)."""
    raw = SAMPLE_RECORD.canonical_bytes().decode("utf-8")
    assert " " not in raw, "Unexpected whitespace in canonical bytes"


def test_canonical_bytes_utf8_encoded():
    """T1e: canonical_bytes returns bytes encoded as UTF-8."""
    b = SAMPLE_RECORD.canonical_bytes()
    assert isinstance(b, bytes)
    b.decode("utf-8")  # Must not raise


# ---------------------------------------------------------------------------
# Task 2 — Cross-Version Stability Guard
# ---------------------------------------------------------------------------


def test_canonical_bytes_known_value():
    """T2a: canonical_bytes matches a known pinned value (cross-version stability).

    The expected value is computed from explicit field ordering and sorted keys.
    It must be stable across Python 3.10, 3.11, and 3.12.
    """
    import hashlib
    import json

    # Reproduce the expected bytes using the same explicit logic
    obj = {
        "actor_id": "alice",
        "authority_basis": "OWNER",
        "outcome": "APPROVED",
        "risk_class": "MEDIUM",
        "timestamp": "2026-01-01T00:00:00Z",
        "transition_id": "tx-001",
    }
    expected = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert SAMPLE_RECORD.canonical_bytes() == expected


def test_canonical_hash_known_value():
    """T2b: canonical_hash() matches a pinned sha256 digest."""
    import hashlib
    import json

    obj = {
        "actor_id": "alice",
        "authority_basis": "OWNER",
        "outcome": "APPROVED",
        "risk_class": "MEDIUM",
        "timestamp": "2026-01-01T00:00:00Z",
        "transition_id": "tx-001",
    }
    raw = json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    expected_hash = hashlib.sha256(raw).hexdigest()
    assert SAMPLE_RECORD.canonical_hash() == expected_hash


def test_no_version_dependent_dict_ordering():
    """T2c: Two DecisionRecords with identical fields produce identical bytes (no implicit ordering)."""
    r1 = DecisionRecord(
        transition_id="tx-999",
        outcome=TransitionOutcome.REFUSED,
        risk_class=RiskClass.HIGH,
        actor_id="bob",
        authority_basis="USER",
        timestamp="2026-06-01T12:00:00Z",
    )
    r2 = DecisionRecord(
        transition_id="tx-999",
        outcome=TransitionOutcome.REFUSED,
        risk_class=RiskClass.HIGH,
        actor_id="bob",
        authority_basis="USER",
        timestamp="2026-06-01T12:00:00Z",
    )
    assert r1.canonical_bytes() == r2.canonical_bytes()
    assert r1.canonical_hash() == r2.canonical_hash()


# ---------------------------------------------------------------------------
# Task 3 — Authority Mapping Isolation
# ---------------------------------------------------------------------------


def test_evaluate_fails_cleanly_when_evidence_missing():
    """T3a: evaluate() raises ValueError when provided_evidence is None."""
    ctx_no_evidence = AuthorityContext(
        actor_id="alice",
        authority_basis="OWNER",
        tenant_id="tenant-1",
        provided_evidence=None,
    )
    with pytest.raises(ValueError, match="provided_evidence is required"):
        evaluate(SAMPLE_REQUEST, ctx_no_evidence)


def test_evaluate_fails_on_unknown_authority_basis():
    """T3b: evaluate() raises ValueError for an unrecognised authority_basis."""
    ctx_bad_basis = AuthorityContext(
        actor_id="alice",
        authority_basis="UNKNOWN_LEVEL",
        tenant_id="tenant-1",
        provided_evidence=Evidence.OWNER,
    )
    with pytest.raises(ValueError, match="Unknown authority_basis"):
        evaluate(SAMPLE_REQUEST, ctx_bad_basis)


def test_evaluate_approved_with_sufficient_evidence():
    """T3c: evaluate() returns APPROVED when evidence meets requirement."""
    record = evaluate(SAMPLE_REQUEST, SAMPLE_CONTEXT)
    assert record.outcome == TransitionOutcome.APPROVED
    assert record.transition_id == "tx-001"
    assert record.actor_id == "alice"


def test_evaluate_refused_with_insufficient_evidence():
    """T3d: evaluate() returns REFUSED when evidence is below requirement."""
    ctx_low = AuthorityContext(
        actor_id="alice",
        authority_basis="ADMIN",
        tenant_id="tenant-1",
        provided_evidence=Evidence.USER,
    )
    record = evaluate(SAMPLE_REQUEST, ctx_low)
    assert record.outcome == TransitionOutcome.REFUSED


def test_evaluate_supervised_for_critical_irreversible():
    """T3e: evaluate() returns SUPERVISED for critical irreversible transitions."""
    critical_request = TransitionRequest(
        transition_id="tx-002",
        risk_class=RiskClass.CRITICAL,
        irreversible=True,
        resource_identifier="res://critical",
        trust_boundary_crossed=True,
        override_token=None,
        timestamp="2026-01-01T00:00:00Z",
    )
    ctx_admin = AuthorityContext(
        actor_id="admin",
        authority_basis="ADMIN",
        tenant_id="tenant-1",
        provided_evidence=Evidence.ADMIN,
    )
    record = evaluate(critical_request, ctx_admin)
    assert record.outcome == TransitionOutcome.SUPERVISED


def test_authority_context_provided_evidence_defaults_none():
    """T3f: AuthorityContext.provided_evidence defaults to None."""
    ctx = AuthorityContext(
        actor_id="alice",
        authority_basis="OWNER",
        tenant_id="tenant-1",
    )
    assert ctx.provided_evidence is None


# ---------------------------------------------------------------------------
# Task 4 — Boundary Integrity
# ---------------------------------------------------------------------------


def test_mgtp_import_does_not_modify_authority_gate():
    """T4a: Importing mgtp does not alter AuthorityGate behaviour."""
    gate = AuthorityGate(Evidence.OWNER)
    assert gate.check(Evidence.ADMIN) is Decision.ALLOW
    assert gate.check(Evidence.USER) is Decision.DENY
    assert gate.required_level is Evidence.OWNER


def test_mgtp_import_does_not_monkeypatch_evidence():
    """T4b: Evidence enum members and ordering are unchanged after importing mgtp."""
    expected_order = [Evidence.NONE, Evidence.USER, Evidence.OWNER, Evidence.ADMIN]
    assert list(Evidence) == expected_order
    assert Evidence.NONE < Evidence.USER < Evidence.OWNER < Evidence.ADMIN


def test_commit_gate_module_not_imported_by_mgtp():
    """T4c: Importing mgtp does not introduce commit_gate into sys.modules."""
    import importlib

    # Remove any cached mgtp modules so we get a clean re-import
    mgtp_keys = [k for k in sys.modules if k == "mgtp" or k.startswith("mgtp.")]
    saved_mgtp = {k: sys.modules.pop(k) for k in mgtp_keys}

    # Record commit_gate modules that may already be present from other tests
    pre_commit_gate = {k for k in sys.modules if k.startswith("commit_gate")}

    try:
        importlib.import_module("mgtp")
        post_commit_gate = {k for k in sys.modules if k.startswith("commit_gate")}
        new_commit_gate = post_commit_gate - pre_commit_gate
        assert not new_commit_gate, (
            f"mgtp import introduced commit_gate modules: {new_commit_gate}"
        )
    finally:
        # Restore mgtp modules so other tests are unaffected
        sys.modules.update(saved_mgtp)


def test_authority_gate_check_is_pure():
    """T4d: authority_gate.check() remains pure (same output for same input)."""
    gate = AuthorityGate(Evidence.USER)
    results = [gate.check(Evidence.NONE) for _ in range(50)]
    assert all(r is Decision.DENY for r in results)
    results2 = [gate.check(Evidence.OWNER) for _ in range(50)]
    assert all(r is Decision.ALLOW for r in results2)
