"""Tests T4-T6: Authority drift detection."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from commit_gate.drift import build_authority_graph, detect_drift


BASELINE_GRAPH = {"ricky": ["FILE"]}
INVARIANT_HASH = "contract_v1_hash"


def test_t4_drift_fail_expansion_without_contract_revision():
    """T4: Adding one allow edge without invariant_hash change => FAIL."""
    expanded_graph = {"ricky": ["DEPLOY", "FILE"]}
    result = detect_drift(
        baseline_graph=BASELINE_GRAPH,
        current_graph=expanded_graph,
        baseline_invariant_hash=INVARIANT_HASH,
        current_invariant_hash=INVARIANT_HASH,
        acknowledge_expansion=False,
    )
    assert result["pass"] is False, "Should FAIL on reachability expansion"
    assert result["reason"] == "reachability_expansion_without_contract_revision"
    assert len(result["added_edges"]) > 0


def test_t5_drift_pass_tightening():
    """T5: Removing edges => PASS."""
    tightened_graph = {}
    result = detect_drift(
        baseline_graph=BASELINE_GRAPH,
        current_graph=tightened_graph,
        baseline_invariant_hash=INVARIANT_HASH,
        current_invariant_hash=INVARIANT_HASH,
    )
    assert result["pass"] is True, "Should PASS on tightening"
    assert result["reason"] == "no_expansion"
    assert len(result["removed_edges"]) > 0


def test_t6_drift_pass_expansion_with_acknowledged_revision():
    """T6: Expansion allowed when invariant_hash changes AND acknowledge_expansion=True."""
    expanded_graph = {"ricky": ["DEPLOY", "FILE"]}
    new_hash = "contract_v2_hash"
    result = detect_drift(
        baseline_graph=BASELINE_GRAPH,
        current_graph=expanded_graph,
        baseline_invariant_hash=INVARIANT_HASH,
        current_invariant_hash=new_hash,
        acknowledge_expansion=True,
    )
    assert result["pass"] is True, "Should PASS with acknowledged expansion"
    assert result["reason"] == "expansion_acknowledged_with_contract_revision"


def test_t6_drift_fail_expansion_not_acknowledged():
    """T6 negative: Expansion with new hash but no acknowledgement => FAIL."""
    expanded_graph = {"ricky": ["DEPLOY", "FILE"]}
    new_hash = "contract_v2_hash"
    result = detect_drift(
        baseline_graph=BASELINE_GRAPH,
        current_graph=expanded_graph,
        baseline_invariant_hash=INVARIANT_HASH,
        current_invariant_hash=new_hash,
        acknowledge_expansion=False,
    )
    assert result["pass"] is False
    assert result["reason"] == "expansion_with_contract_revision_but_not_acknowledged"


def test_no_change_passes():
    """Identical graphs => PASS."""
    result = detect_drift(
        baseline_graph=BASELINE_GRAPH,
        current_graph=BASELINE_GRAPH,
        baseline_invariant_hash=INVARIANT_HASH,
        current_invariant_hash=INVARIANT_HASH,
    )
    assert result["pass"] is True
    assert result["reason"] == "no_expansion"


def test_build_authority_graph():
    """Graph built from ruleset contains only allowlist edges."""
    ruleset = {
        "allowlist": [
            {"actor_id": "ricky", "action_class": "FILE", "scope_match": {}},
            {"actor_id": "ricky", "action_class": "SEND", "scope_match": {}},
        ],
        "denylist": [{"actor_id": "ricky", "action_class": "DEPLOY", "scope_match": {}}],
        "escalation": [],
    }
    graph = build_authority_graph(ruleset)
    assert "ricky" in graph
    assert sorted(graph["ricky"]) == ["FILE", "SEND"]
    assert "DEPLOY" not in graph.get("ricky", [])
