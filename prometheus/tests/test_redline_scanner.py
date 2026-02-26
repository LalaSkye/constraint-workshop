"""Tests for red-line scanner."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prometheus.redlines import scan_prometheus_redlines, find_forbidden

_PROMETHEUS_ROOT = os.path.join(os.path.dirname(__file__), "..")

_RULES = {
    "forbidden_paths": ["/trinity/gate/", "/alviantech/pipeline/"],
    "forbidden_tokens": ["ALLOW", "HOLD", "DENY", "SILENCE"],
    "case_insensitive": True,
    "include_globs": ["src/**/*.py"],
}


def test_clean_codebase_zero_findings():
    result = scan_prometheus_redlines(_PROMETHEUS_ROOT, _RULES)
    assert len(result["findings"]) == 0, (
        f"Expected 0 redline findings in Prometheus code, got {len(result['findings'])}: "
        f"{result['findings']}"
    )


def test_find_forbidden_detects_token():
    findings = find_forbidden(
        "This line says DENY something",
        forbidden_paths=[], forbidden_tokens=["DENY"],
        case_insensitive=True,
    )
    assert len(findings) == 1
    assert findings[0]["kind"] == "FORBIDDEN_TOKEN"
    assert findings[0]["match"] == "DENY"


def test_find_forbidden_detects_path():
    findings = find_forbidden(
        "import from /trinity/gate/module",
        forbidden_paths=["/trinity/gate/"], forbidden_tokens=[],
        case_insensitive=True,
    )
    assert len(findings) == 1
    assert findings[0]["kind"] == "FORBIDDEN_PATH"


def test_find_forbidden_case_insensitive():
    findings = find_forbidden(
        "this line says deny quietly",
        forbidden_paths=[], forbidden_tokens=["DENY"],
        case_insensitive=True,
    )
    assert len(findings) == 1


def test_scanner_ignores_fixtures():
    """Scanner must NOT scan fixtures/ or expected/ directories."""
    result = scan_prometheus_redlines(_PROMETHEUS_ROOT, _RULES)
    for finding in result["findings"]:
        assert not finding["path"].startswith("fixtures/")
        assert not finding["path"].startswith("expected/")
