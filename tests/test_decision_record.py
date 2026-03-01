"""Tests for mgtp.decision_record — determinism and structural correctness."""

import hashlib
import json

import pytest

from mgtp.decision_record import DecisionRecord
from mgtp.types import TransitionOutcome


_COMMON_KWARGS = dict(
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


def test_build_returns_decision_record():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    assert isinstance(rec, DecisionRecord)


def test_decision_id_is_string():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    assert isinstance(rec.decision_id, str)
    assert len(rec.decision_id) == 36  # UUID5 format


def test_canonical_bytes_are_bytes():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    assert isinstance(rec.canonical_bytes, bytes)


def test_content_hash_is_hex_sha256():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    assert isinstance(rec.content_hash, str)
    assert len(rec.content_hash) == 64
    # Verify it matches sha256 of canonical_bytes
    expected = hashlib.sha256(rec.canonical_bytes).hexdigest()
    assert rec.content_hash == expected


def test_canonical_bytes_are_valid_json():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    parsed = json.loads(rec.canonical_bytes)
    assert parsed["transition_id"] == "TOOL_CALL_HTTP"
    assert parsed["outcome"] == TransitionOutcome.APPROVED.value


def test_canonical_bytes_use_sorted_keys():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    parsed = json.loads(rec.canonical_bytes.decode("utf-8"))
    keys = list(parsed.keys())
    assert keys == sorted(keys)


def test_canonical_bytes_use_compact_separators():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    raw = rec.canonical_bytes.decode("utf-8")
    # Compact separators: no spaces after ':' or ','
    assert ": " not in raw
    assert ", " not in raw


def test_determinism_same_inputs_same_decision_id():
    rec1 = DecisionRecord.build(**_COMMON_KWARGS)
    rec2 = DecisionRecord.build(**_COMMON_KWARGS)
    assert rec1.decision_id == rec2.decision_id


def test_determinism_same_inputs_same_canonical_bytes():
    rec1 = DecisionRecord.build(**_COMMON_KWARGS)
    rec2 = DecisionRecord.build(**_COMMON_KWARGS)
    assert rec1.canonical_bytes == rec2.canonical_bytes


def test_determinism_same_inputs_same_content_hash():
    rec1 = DecisionRecord.build(**_COMMON_KWARGS)
    rec2 = DecisionRecord.build(**_COMMON_KWARGS)
    assert rec1.content_hash == rec2.content_hash


def test_different_context_hash_produces_different_decision_id():
    rec1 = DecisionRecord.build(**_COMMON_KWARGS)
    rec2 = DecisionRecord.build(**{**_COMMON_KWARGS, "context_hash": "different-hash"})
    assert rec1.decision_id != rec2.decision_id


def test_different_context_hash_produces_different_content_hash():
    rec1 = DecisionRecord.build(**_COMMON_KWARGS)
    rec2 = DecisionRecord.build(**{**_COMMON_KWARGS, "context_hash": "different-hash"})
    assert rec1.content_hash != rec2.content_hash


def test_all_required_fields_present():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    assert rec.transition_id == "TOOL_CALL_HTTP"
    assert rec.actor_id == "user-42"
    assert rec.tenant_id == "tenant-99"
    assert rec.authority_basis == "OWNER"
    assert rec.risk_class == "HIGH"
    assert rec.outcome is TransitionOutcome.APPROVED
    assert rec.reason_code == "APPROVED"
    assert rec.timestamp == "2025-01-01T00:00:00Z"
    assert rec.gate_version == "v0.2"
    assert rec.context_hash == "abc123"


def test_record_is_immutable():
    rec = DecisionRecord.build(**_COMMON_KWARGS)
    with pytest.raises((AttributeError, TypeError)):
        rec.transition_id = "OTHER"  # type: ignore[misc]
