"""Tests for mgtp.decision_record / mgtp.types.DecisionRecord.

There is exactly one DecisionRecord implementation (mgtp.types.DecisionRecord).
mgtp.decision_record re-exports it; both import paths are tested here to confirm
there is no duplicate or competing class.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

# Ensure the repo root is on sys.path so authority_gate can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mgtp.decision_record import DecisionRecord as DR_from_decision_record
from mgtp.types import DecisionRecord, TransitionOutcome, RiskClass


_COMMON = dict(
    transition_id="TOOL_CALL_HTTP",
    actor_id="user-42",
    tenant_id="tenant-99",
    authority_basis="OWNER",
    risk_class="HIGH",
    outcome=TransitionOutcome.APPROVED,
    reason_code="APPROVED",
    timestamp="2025-01-01T00:00:00Z",
    gate_version="v0.2",
    context_hash="abc123",
)


# ---------------------------------------------------------------------------
# Single canonical class (no duplicate)
# ---------------------------------------------------------------------------


def test_single_implementation_same_object():
    """mgtp.decision_record.DecisionRecord is the same class as mgtp.types.DecisionRecord."""
    assert DR_from_decision_record is DecisionRecord


# ---------------------------------------------------------------------------
# build() factory
# ---------------------------------------------------------------------------


def test_build_returns_decision_record():
    rec = DecisionRecord.build(**_COMMON)
    assert isinstance(rec, DecisionRecord)


def test_build_stores_reason_as_reason_code():
    rec = DecisionRecord.build(**_COMMON)
    assert rec.reason == "APPROVED"
    assert rec.reason_code == "APPROVED"


def test_build_accepts_string_risk_class():
    rec = DecisionRecord.build(**_COMMON)
    assert rec.risk_class == RiskClass.HIGH
    assert rec.risk_class == "HIGH"  # str Enum equality


def test_build_accepts_enum_risk_class():
    kwargs = {**_COMMON, "risk_class": RiskClass.HIGH}
    rec = DecisionRecord.build(**kwargs)
    assert rec.risk_class == RiskClass.HIGH


# ---------------------------------------------------------------------------
# Record is immutable
# ---------------------------------------------------------------------------


def test_record_is_immutable():
    rec = DecisionRecord.build(**_COMMON)
    with pytest.raises((AttributeError, TypeError)):
        rec.transition_id = "OTHER"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# canonical_bytes property
# ---------------------------------------------------------------------------


def test_canonical_bytes_are_bytes():
    rec = DecisionRecord.build(**_COMMON)
    assert isinstance(rec.canonical_bytes, bytes)


def test_canonical_bytes_are_valid_json():
    rec = DecisionRecord.build(**_COMMON)
    parsed = json.loads(rec.canonical_bytes)
    assert parsed["transition_id"] == "TOOL_CALL_HTTP"
    assert parsed["outcome"] == TransitionOutcome.APPROVED.value


def test_canonical_bytes_sorted_keys():
    rec = DecisionRecord.build(**_COMMON)
    keys = list(json.loads(rec.canonical_bytes).keys())
    assert keys == sorted(keys)


def test_canonical_bytes_compact_separators():
    rec = DecisionRecord.build(**_COMMON)
    raw = rec.canonical_bytes.decode("utf-8")
    assert ": " not in raw
    assert ", " not in raw


def test_to_canonical_json_alias():
    rec = DecisionRecord.build(**_COMMON)
    assert rec.to_canonical_json() == rec.canonical_bytes


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_determinism_same_inputs_same_canonical_bytes():
    r1 = DecisionRecord.build(**_COMMON)
    r2 = DecisionRecord.build(**_COMMON)
    assert r1.canonical_bytes == r2.canonical_bytes


def test_determinism_same_inputs_same_content_hash():
    r1 = DecisionRecord.build(**_COMMON)
    r2 = DecisionRecord.build(**_COMMON)
    assert r1.content_hash == r2.content_hash


def test_determinism_same_inputs_same_decision_id():
    r1 = DecisionRecord.build(**_COMMON)
    r2 = DecisionRecord.build(**_COMMON)
    assert r1.decision_id == r2.decision_id


def test_different_context_hash_produces_different_decision_id():
    r1 = DecisionRecord.build(**_COMMON)
    r2 = DecisionRecord.build(**{**_COMMON, "context_hash": "different"})
    assert r1.decision_id != r2.decision_id


# ---------------------------------------------------------------------------
# content_hash is sha256 of canonical_bytes
# ---------------------------------------------------------------------------


def test_content_hash_matches_sha256():
    rec = DecisionRecord.build(**_COMMON)
    expected = hashlib.sha256(rec.canonical_bytes).hexdigest()
    assert rec.content_hash == expected


def test_content_hash_is_64_hex_chars():
    rec = DecisionRecord.build(**_COMMON)
    assert len(rec.content_hash) == 64
    assert rec.content_hash == rec.content_hash.lower()


# ---------------------------------------------------------------------------
# decision_id
# ---------------------------------------------------------------------------


def test_decision_id_is_uuid_format():
    rec = DecisionRecord.build(**_COMMON)
    assert isinstance(rec.decision_id, str)
    assert len(rec.decision_id) == 36  # UUID5


def test_decision_id_empty_when_no_context_hash():
    rec = DecisionRecord(
        transition_id="x",
        outcome=TransitionOutcome.APPROVED,
        authority_basis="OWNER",
        risk_class=RiskClass.LOW,
        reason="authority_sufficient",
    )
    assert rec.decision_id == ""


# ---------------------------------------------------------------------------
# Simple 5-field construction (used by evaluate())
# ---------------------------------------------------------------------------


def test_simple_construction():
    rec = DecisionRecord(
        transition_id="tx-1",
        outcome=TransitionOutcome.REFUSED,
        authority_basis="USER",
        risk_class=RiskClass.HIGH,
        reason="authority_insufficient",
    )
    assert rec.reason_code == "authority_insufficient"
    assert rec.actor_id == ""
    assert rec.context_hash == ""
    assert rec.decision_id == ""


def test_all_required_fields_present():
    rec = DecisionRecord.build(**_COMMON)
    assert rec.transition_id == "TOOL_CALL_HTTP"
    assert rec.actor_id == "user-42"
    assert rec.tenant_id == "tenant-99"
    assert rec.authority_basis == "OWNER"
    assert rec.outcome is TransitionOutcome.APPROVED
    assert rec.timestamp == "2025-01-01T00:00:00Z"
    assert rec.gate_version == "v0.2"
    assert rec.context_hash == "abc123"
