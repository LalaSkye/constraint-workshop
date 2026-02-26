"""Negative tests: prove the scanner bites when it should.

Creates temp directories with injected forbidden tokens/paths
and asserts the scanner and fit report detect them correctly.
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prometheus.redlines import scan_prometheus_redlines
from prometheus.fit_report import classify, build_fit_report


_RULES = {
    "forbidden_paths": ["/trinity/gate/", "/alviantech/pipeline/"],
    "forbidden_tokens": ["ALLOW", "HOLD", "DENY", "SILENCE"],
    "case_insensitive": True,
    "include_globs": ["src/**/*.py"],
}


def _make_temp_prometheus(files):
    """Create a temp prometheus dir with given src files.

    files is a dict of {relative_path: content}.
    Returns the temp directory path (caller must clean up).
    """
    tmp = tempfile.mkdtemp(prefix="prom_neg_")
    for rel, content in files.items():
        full = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
    return tmp


def test_forbidden_token_detected():
    """Injecting a forbidden token into src triggers a finding."""
    tmp = _make_temp_prometheus({
        "src/prometheus/evil.py": "# This module tries to ALLOW things.\n",
    })
    try:
        result = scan_prometheus_redlines(tmp, _RULES)
        assert len(result["findings"]) >= 1
        kinds = {f["kind"] for f in result["findings"]}
        assert "FORBIDDEN_TOKEN" in kinds
    finally:
        shutil.rmtree(tmp)


def test_forbidden_path_detected():
    """Injecting a forbidden path into src triggers a finding."""
    tmp = _make_temp_prometheus({
        "src/prometheus/leak.py": "# imports from /trinity/gate/ are banned\n",
    })
    try:
        result = scan_prometheus_redlines(tmp, _RULES)
        assert len(result["findings"]) >= 1
        kinds = {f["kind"] for f in result["findings"]}
        assert "FORBIDDEN_PATH" in kinds
    finally:
        shutil.rmtree(tmp)


def test_injection_causes_drift_risk():
    """Redline findings produce DRIFT_RISK verdict."""
    verdict = classify(
        valid_count=10,
        invalid_count=0,
        redline_finding_count=1,
        invalid_with_forbidden=0,
    )
    assert verdict == "DRIFT_RISK"


def test_forbidden_content_in_invalid_causes_drift_risk():
    """Forbidden content in invalid events produces DRIFT_RISK."""
    verdict = classify(
        valid_count=10,
        invalid_count=2,
        redline_finding_count=0,
        invalid_with_forbidden=1,
    )
    assert verdict == "DRIFT_RISK"


def test_clean_src_has_no_findings():
    """Clean src with no forbidden content has zero findings."""
    tmp = _make_temp_prometheus({
        "src/prometheus/clean.py": "# This is a perfectly clean module.\ndef hello():\n    return 42\n",
    })
    try:
        result = scan_prometheus_redlines(tmp, _RULES)
        assert len(result["findings"]) == 0
    finally:
        shutil.rmtree(tmp)
