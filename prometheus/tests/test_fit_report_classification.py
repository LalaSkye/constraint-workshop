"""Tests for fit report classification."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prometheus.fit_report import classify, build_fit_report


def test_fit_clean():
    assert classify(valid_count=10, invalid_count=0, redline_finding_count=0, invalid_with_forbidden=0) == "FIT_CLEAN"


def test_fit_with_warnings():
    assert classify(valid_count=8, invalid_count=2, redline_finding_count=0, invalid_with_forbidden=0) == "FIT_WITH_WARNINGS"


def test_drift_risk_via_redline():
    assert classify(valid_count=10, invalid_count=0, redline_finding_count=1, invalid_with_forbidden=0) == "DRIFT_RISK"


def test_drift_risk_via_invalid_with_forbidden():
    assert classify(valid_count=9, invalid_count=1, redline_finding_count=0, invalid_with_forbidden=1) == "DRIFT_RISK"


def test_drift_risk_takes_priority_over_warnings():
    assert classify(valid_count=8, invalid_count=2, redline_finding_count=1, invalid_with_forbidden=0) == "DRIFT_RISK"


def test_build_fit_report_keys():
    report = build_fit_report(
        input_hash="abc123", valid_count=10, invalid_count=0,
        redline_finding_count=0, invalid_with_forbidden=0,
    )
    expected_keys = {"verdict", "input_hash", "schema_invalid_count",
                     "redline_finding_count", "invalid_with_forbidden_count", "notes"}
    assert set(report.keys()) == expected_keys
    assert report["verdict"] == "FIT_CLEAN"


def test_build_fit_report_notes_default_empty():
    report = build_fit_report(
        input_hash="abc", valid_count=1, invalid_count=0,
        redline_finding_count=0, invalid_with_forbidden=0,
    )
    assert report["notes"] == []
