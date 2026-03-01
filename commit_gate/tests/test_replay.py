"""Test R4: Replay demonstration — fixed fixture produces pinned decision_hash."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from commit_gate.engine import evaluate, load_ruleset

_FIXTURE = Path(__file__).resolve().parent.parent / "baselines" / "fixtures" / "fixed_request.json"
_RULESET = Path(__file__).resolve().parent.parent / "rules" / "ruleset.json"


def test_replay_decision_hash_pinned():
    """R4: Replaying fixed_request.json against ruleset.json must yield pinned decision_hash."""
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    ruleset = load_ruleset(_RULESET)

    result = evaluate(fixture["request"], ruleset)

    assert result["verdict"] == fixture["expected_verdict"]
    assert result["request_hash"] == fixture["expected_request_hash"], (
        f"request_hash changed: got {result['request_hash']!r}"
    )
    assert result["decision_hash"] == fixture["expected_decision_hash"], (
        f"decision_hash changed: got {result['decision_hash']!r}"
    )


def test_replay_is_idempotent():
    """R4: Replaying the same fixture twice produces identical decision_hash."""
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    ruleset = load_ruleset(_RULESET)

    r1 = evaluate(fixture["request"], ruleset)
    r2 = evaluate(fixture["request"], ruleset)

    assert r1["decision_hash"] == r2["decision_hash"]
    assert r1["request_hash"] == r2["request_hash"]