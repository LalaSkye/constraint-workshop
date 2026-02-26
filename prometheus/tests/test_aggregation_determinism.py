"""Tests for aggregation determinism."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prometheus.aggregate import compute_window_from_events, summarise


_SAMPLE_EVENTS = [
    {"event_type": "startup", "ts": "2025-02-26T10:00:00Z", "source": "unit-test", "severity": "INFO", "message": "ok", "context": None},
    {"event_type": "heartbeat", "ts": "2025-02-26T10:05:00Z", "source": "unit-test", "severity": "INFO", "message": "ok", "context": None},
    {"event_type": "latency_spike", "ts": "2025-02-26T10:10:00Z", "source": "unit-test", "severity": "WARN", "message": "ok", "context": None},
]


def test_summarise_identical_for_identical_inputs():
    s1 = summarise(_SAMPLE_EVENTS, "2025-02-26T10:00:00Z", "2025-02-26T10:10:00Z", "abc123")
    s2 = summarise(_SAMPLE_EVENTS, "2025-02-26T10:00:00Z", "2025-02-26T10:10:00Z", "abc123")
    assert json.dumps(s1, sort_keys=True) == json.dumps(s2, sort_keys=True)


def test_window_from_events():
    start, end = compute_window_from_events(_SAMPLE_EVENTS)
    assert start == "2025-02-26T10:00:00Z"
    assert end == "2025-02-26T10:10:00Z"


def test_empty_window():
    start, end = compute_window_from_events([])
    assert start == "1970-01-01T00:00:00Z"
    assert end == "1970-01-01T00:00:00Z"


def test_top_sources_sorted():
    events = [
        {"event_type": "a", "ts": "2025-01-01T00:00:00Z", "source": "beta", "severity": "INFO", "message": "ok", "context": None},
        {"event_type": "a", "ts": "2025-01-01T00:00:00Z", "source": "alpha", "severity": "INFO", "message": "ok", "context": None},
        {"event_type": "a", "ts": "2025-01-01T00:00:00Z", "source": "alpha", "severity": "INFO", "message": "ok", "context": None},
    ]
    s = summarise(events, "2025-01-01T00:00:00Z", "2025-01-01T00:00:00Z", "hash")
    assert s["top_sources"][0]["source"] == "alpha"
    assert s["top_sources"][0]["count"] == 2
    assert s["top_sources"][1]["source"] == "beta"


def test_counts_by_type_keys_sorted():
    s = summarise(_SAMPLE_EVENTS, "2025-02-26T10:00:00Z", "2025-02-26T10:10:00Z", "hash")
    keys = list(s["counts_by_type"].keys())
    assert keys == sorted(keys)
