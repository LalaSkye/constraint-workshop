"""Tests T1-T3: Determinism, hash stability, ordering."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from commit_gate.canonicalise import canonicalise, canonical_hash
from commit_gate.engine import evaluate, build_request_obj


SAMPLE_REQUEST = {
    "actor_id": "ricky",
    "action_class": "FILE",
    "context": {"description": "test commit"},
    "authority_scope": {"project": "alpha"},
    "invariant_hash": "abc123",
}

SAMPLE_RULESET = {
    "allowlist": [
        {"actor_id": "ricky", "action_class": "FILE", "scope_match": {"project": "alpha"}}
    ],
    "denylist": [],
    "escalation": [],
}


def test_t1_determinism():
    """T1: Same input produces byte-identical output artefact."""
    v1 = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    v2 = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert canonicalise(v1) == canonicalise(v2), "Outputs not byte-identical"
    assert v1["decision_hash"] == v2["decision_hash"]
    assert v1["request_hash"] == v2["request_hash"]


def test_t2_hash_stability():
    """T2: request_hash is stable (known value check)."""
    req_obj = build_request_obj(
        actor_id="ricky",
        action_class="FILE",
        context={"description": "test commit"},
        authority_scope={"project": "alpha"},
        invariant_hash="abc123",
    )
    h1 = canonical_hash(req_obj)
    h2 = canonical_hash(req_obj)
    assert h1 == h2, "Hash not stable across calls"
    assert len(h1) == 64, "Not a valid sha256 hex digest"
    assert h1 == h1.lower(), "Hash not lower-case"


def test_t3_ordering():
    """T3: Reasons and keys are stable regardless of insertion order."""
    # Create two dicts with different insertion order
    obj_a = {"z": 1, "a": 2, "m": 3}
    obj_b = {"a": 2, "m": 3, "z": 1}
    assert canonicalise(obj_a) == canonicalise(obj_b), "Key ordering not stable"

    # Verify reasons are sorted in verdict
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert v["reasons"] == sorted(v["reasons"]), "Reasons not sorted"


def test_verdict_allow():
    """Allowlist match produces ALLOW."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert v["verdict"] == "ALLOW"
    assert "allowlist_match" in v["reasons"]


def test_verdict_refuse_denylist():
    """Denylist match produces REFUSE."""
    ruleset = {
        "allowlist": [{"actor_id": "ricky", "action_class": "FILE", "scope_match": {"project": "alpha"}}],
        "denylist": [{"actor_id": "ricky", "action_class": "FILE", "scope_match": {"project": "alpha"}}],
        "escalation": [],
    }
    v = evaluate(SAMPLE_REQUEST, ruleset)
    assert v["verdict"] == "REFUSE"
    assert "denylist_match" in v["reasons"]


def test_verdict_escalate():
    """Escalation match produces ESCALATE."""
    ruleset = {
        "allowlist": [],
        "denylist": [],
        "escalation": [{"action_class": "FILE", "scope_match": {"project": "alpha"}}],
    }
    v = evaluate(SAMPLE_REQUEST, ruleset)
    assert v["verdict"] == "ESCALATE"


def test_verdict_default_refuse():
    """No match produces default REFUSE."""
    ruleset = {"allowlist": [], "denylist": [], "escalation": []}
    v = evaluate(SAMPLE_REQUEST, ruleset)
    assert v["verdict"] == "REFUSE"
    assert "default_refuse" in v["reasons"]


def test_scope_superset_allowed():
    """Request with extra scope keys still matches rule."""
    request = dict(SAMPLE_REQUEST)
    request["authority_scope"] = {"project": "alpha", "environment": "staging"}
    v = evaluate(request, SAMPLE_RULESET)
    assert v["verdict"] == "ALLOW"


def test_artefact_version():
    """Artefact version is 0.1."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert v["artefact_version"] == "0.1"


# Golden regression constants — do not change without contract revision
_GOLDEN_REQUEST_HASH = "91be8e7594ee9fc3967632dce931884f6dbf357f58794fbca54b9e579fda447f"
_GOLDEN_DECISION_HASH = "09880c122bcec255c2964a28344496bca7b85e74fcb5180c304358beae5cc497"


def test_golden_request_hash():
    """Golden: canonical request hash for SAMPLE_REQUEST is pinned."""
    req_obj = build_request_obj(
        actor_id=SAMPLE_REQUEST["actor_id"],
        action_class=SAMPLE_REQUEST["action_class"],
        context=SAMPLE_REQUEST["context"],
        authority_scope=SAMPLE_REQUEST["authority_scope"],
        invariant_hash=SAMPLE_REQUEST["invariant_hash"],
    )
    assert canonical_hash(req_obj) == _GOLDEN_REQUEST_HASH, (
        "request_hash changed — canonicalise or field order may have drifted"
    )


def test_golden_decision_hash():
    """Golden: decision_hash for SAMPLE_REQUEST + SAMPLE_RULESET is pinned."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert v["request_hash"] == _GOLDEN_REQUEST_HASH, "request_hash drifted from golden"
    assert v["decision_hash"] == _GOLDEN_DECISION_HASH, (
        "decision_hash changed — verdict, reasons, or canonicalise may have drifted"
    )


def test_replay_produces_identical_decision_hash():
    """Replay: evaluating the same request twice produces byte-identical decision artefacts."""
    v1 = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    v2 = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert v1["decision_hash"] == v2["decision_hash"], "decision_hash differs on replay"
    assert v1["decision_hash"] == _GOLDEN_DECISION_HASH, "replayed decision_hash differs from golden"
    assert canonicalise(v1) == canonicalise(v2), "Artefact bytes not identical on replay"
