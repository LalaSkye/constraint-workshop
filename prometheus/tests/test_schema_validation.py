"""Tests for schema validation."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prometheus.schemas import validate_diag_event, validate_diag_events
from prometheus.io_jsonl import read_jsonl

_FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def test_normal_fixtures_all_valid():
    events = read_jsonl(os.path.join(_FIXTURES, "normal_events.jsonl"))
    valid, invalid = validate_diag_events(events)
    assert len(invalid) == 0
    assert len(valid) == 4


def test_bad_schema_fixtures_three_invalid():
    events = read_jsonl(os.path.join(_FIXTURES, "bad_events_schema.jsonl"))
    valid, invalid = validate_diag_events(events)
    assert len(invalid) == 3
    assert len(valid) == 1


def test_bad_tokens_fixture_is_schema_valid():
    events = read_jsonl(os.path.join(_FIXTURES, "bad_events_tokens.jsonl"))
    valid, invalid = validate_diag_events(events)
    assert len(invalid) == 0
    assert len(valid) == 1


def test_bad_paths_fixture_is_schema_valid():
    events = read_jsonl(os.path.join(_FIXTURES, "bad_events_paths.jsonl"))
    valid, invalid = validate_diag_events(events)
    assert len(invalid) == 0
    assert len(valid) == 1


def test_unknown_key_is_error():
    event = {
        "event_type": "test", "ts": "2025-01-01T00:00:00Z",
        "source": "unit", "severity": "INFO",
        "message": "ok", "context": None, "extra": True,
    }
    ok, errors = validate_diag_event(event)
    assert not ok
    assert any("unknown keys" in e for e in errors)


def test_missing_message_is_error():
    event = {
        "event_type": "test", "ts": "2025-01-01T00:00:00Z",
        "source": "unit", "severity": "INFO", "context": None,
    }
    ok, errors = validate_diag_event(event)
    assert not ok
    assert any("message" in e for e in errors)


def test_bad_severity_type():
    event = {
        "event_type": "test", "ts": "2025-01-01T00:00:00Z",
        "source": "unit", "severity": 42,
        "message": "ok", "context": None,
    }
    ok, errors = validate_diag_event(event)
    assert not ok
    assert any("severity" in e for e in errors)
