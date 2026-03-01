"""Tests R5: timestamp_utc staleness enforcement (fail-closed)."""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from commit_gate.engine import evaluate, TIMESTAMP_MAX_AGE_SECONDS

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


def _ts(offset_seconds=0):
    """Return ISO 8601 UTC timestamp offset by given seconds from now."""
    ts = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return ts.strftime("%Y-%m-%dT%H:%M:%SZ")


def test_fresh_timestamp_passes():
    """R5: Request with fresh timestamp_utc is evaluated normally."""
    request = dict(SAMPLE_REQUEST, timestamp_utc=_ts(-10))
    v = evaluate(request, SAMPLE_RULESET)
    assert v["verdict"] == "ALLOW"
    assert "timestamp_stale" not in v["reasons"]


def test_stale_timestamp_refuses():
    """R5: Request with stale timestamp_utc is REFUSED fail-closed."""
    stale_ts = _ts(-(TIMESTAMP_MAX_AGE_SECONDS + 1))
    request = dict(SAMPLE_REQUEST, timestamp_utc=stale_ts)
    v = evaluate(request, SAMPLE_RULESET)
    assert v["verdict"] == "REFUSE"
    assert "timestamp_stale" in v["reasons"]


def test_future_timestamp_refuses():
    """R5: Request with future timestamp_utc (negative age) is REFUSED fail-closed."""
    future_ts = _ts(+600)
    request = dict(SAMPLE_REQUEST, timestamp_utc=future_ts)
    v = evaluate(request, SAMPLE_RULESET)
    assert v["verdict"] == "REFUSE"
    assert "timestamp_stale" in v["reasons"]


def test_no_timestamp_passes_normally():
    """R5: Request without timestamp_utc proceeds through normal rule evaluation."""
    request = {k: v for k, v in SAMPLE_REQUEST.items() if k != "timestamp_utc"}
    v = evaluate(request, SAMPLE_RULESET)
    assert v["verdict"] == "ALLOW"
    assert "timestamp_stale" not in v["reasons"]


def test_stale_timestamp_produces_deterministic_hash():
    """R5: Stale refusal produces stable decision_hash across multiple calls."""
    stale_ts = _ts(-(TIMESTAMP_MAX_AGE_SECONDS + 86400))
    request = dict(SAMPLE_REQUEST, timestamp_utc=stale_ts)
    v1 = evaluate(request, SAMPLE_RULESET)
    v2 = evaluate(request, SAMPLE_RULESET)
    assert v1["decision_hash"] == v2["decision_hash"]
    assert v1["verdict"] == "REFUSE"
