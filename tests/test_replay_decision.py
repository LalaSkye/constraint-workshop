"""Replay test: proves stored golden canonical bytes are byte-identical on re-evaluation.

T-REPLAY-1: canonical_bytes from fixed inputs == stored golden bytes.
T-REPLAY-2: decision_hash derived from re-evaluation == hash in golden bytes.

Fails if any single byte differs.
"""

import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "commit_gate" / "src"))

from commit_gate.canonicalise import canonicalise
from commit_gate.engine import evaluate

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# Fixed inputs — must exactly match examples/minimal_decision_demo.py
REQUEST = {
    "actor_id": "demo-actor",
    "action_class": "FILE",
    "context": {"description": "minimal demo commit"},
    "authority_scope": {"project": "demo-project"},
    "invariant_hash": "0000000000000000000000000000000000000000000000000000000000000000",
}

RULESET = {
    "allowlist": [
        {
            "actor_id": "demo-actor",
            "action_class": "FILE",
            "scope_match": {"project": "demo-project"},
        }
    ],
    "denylist": [],
    "escalation": [],
}


def _load_golden_bytes():
    b64_text = (FIXTURES_DIR / "golden_canonical_bytes.b64").read_text().strip()
    return base64.b64decode(b64_text)


def test_t_replay_1_canonical_bytes_identical():
    """T-REPLAY-1: Re-evaluating fixed inputs produces byte-identical canonical bytes."""
    golden = _load_golden_bytes()
    result = evaluate(REQUEST, RULESET)
    actual = canonicalise(result)
    assert actual == golden, (
        f"Canonical bytes differ from golden fixture.\n"
        f"Expected: {golden!r}\n"
        f"Got:      {actual!r}"
    )


def test_t_replay_2_decision_hash_stable():
    """T-REPLAY-2: decision_hash in re-evaluated result matches hash in golden bytes."""
    import json

    golden = _load_golden_bytes()
    golden_dict = json.loads(golden.decode("utf-8"))
    golden_hash = golden_dict["decision_hash"]

    result = evaluate(REQUEST, RULESET)
    assert result["decision_hash"] == golden_hash, (
        f"decision_hash mismatch.\n"
        f"Expected: {golden_hash}\n"
        f"Got:      {result['decision_hash']}"
    )
