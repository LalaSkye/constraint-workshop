"""Tests for MGTP evaluate_transition and DecisionRecord."""

import json
import sys
from pathlib import Path

# Ensure the repo root is on the path so authority_gate can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mgtp.evaluate import evaluate_transition
from mgtp.types import (
    AuthorityContext,
    DecisionRecord,
    RiskClass,
    TransitionOutcome,
    TransitionRequest,
)

REGISTRY = {
    "TOOL_CALL_HTTP": {
        "irreversible": True,
        "risk_class": "HIGH",
        "required_authority": "OWNER",
        "gate_version": "v0.2",
    }
}

REQUEST = TransitionRequest(
    transition_id="TOOL_CALL_HTTP",
    risk_class=RiskClass.HIGH,
    irreversible=True,
    resource_identifier="https://example.com",
    trust_boundary_crossed=True,
    override_token=None,
    timestamp="2026-02-28T12:00:00Z",
)

CONTEXT_OWNER = AuthorityContext(
    actor_id="alice",
    authority_basis="OWNER",
    tenant_id="tenant-1",
)

CONTEXT_USER = AuthorityContext(
    actor_id="bob",
    authority_basis="USER",
    tenant_id="tenant-1",
)


def test_approved_when_authority_sufficient():
    record = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    assert record.outcome == TransitionOutcome.APPROVED
    assert record.reason == "authority_sufficient"
    assert record.transition_id == "TOOL_CALL_HTTP"


def test_refused_when_authority_insufficient():
    record = evaluate_transition(REQUEST, CONTEXT_USER, REGISTRY)
    assert record.outcome == TransitionOutcome.REFUSED
    assert record.reason == "authority_insufficient"


def test_refused_when_transition_not_registered():
    request = TransitionRequest(
        transition_id="UNKNOWN_TRANSITION",
        risk_class=RiskClass.LOW,
        irreversible=False,
        resource_identifier="x",
        trust_boundary_crossed=False,
        override_token=None,
        timestamp="2026-02-28T12:00:00Z",
    )
    record = evaluate_transition(request, CONTEXT_OWNER, REGISTRY)
    assert record.outcome == TransitionOutcome.REFUSED
    assert record.reason == "transition_not_registered"


def test_decision_record_is_frozen():
    record = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    assert isinstance(record, DecisionRecord)
    try:
        record.outcome = TransitionOutcome.REFUSED  # type: ignore[misc]
        assert False, "Should raise FrozenInstanceError"
    except Exception:
        pass


def test_canonical_json_sort_keys():
    record = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    raw = record.to_canonical_json()
    parsed = json.loads(raw)
    keys = list(parsed.keys())
    assert keys == sorted(keys), "Keys must be sorted in canonical JSON"


def test_canonical_json_no_whitespace():
    record = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    raw = record.to_canonical_json()
    assert b" " not in raw, "Canonical JSON must have no whitespace"


def test_canonical_json_deterministic():
    r1 = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    r2 = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    assert r1.to_canonical_json() == r2.to_canonical_json()


def test_evaluate_transition_is_deterministic():
    """Same inputs always produce the same DecisionRecord."""
    r1 = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    r2 = evaluate_transition(REQUEST, CONTEXT_OWNER, REGISTRY)
    assert r1 == r2
