"""Tests for JCS canonicalization, reason-code validation, and report envelope.

Covers:
- T-JCS-1: JCS output is byte-stable for identical inputs
- T-JCS-2: JCS output is byte-identical regardless of dict insertion order
- T-JCS-3: validate_reason_codes passes for all known codes
- T-JCS-4: validate_reason_codes fails (ValueError) for any unknown code — fail-closed
- T-JCS-5: evaluate() raises on unknown reason codes reaching the output
- T-JCS-6: report envelope contains required schema fields
- T-JCS-7: write_decision_report uses JCS bytes when serialise=canonicalise_jcs
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from commit_gate.canonicalise import canonicalise, canonicalise_jcs
from commit_gate.engine import (
    KNOWN_REASON_CODES,
    evaluate,
    validate_reason_codes,
    write_decision_report,
)


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


# ---------------------------------------------------------------------------
# T-JCS-1: JCS byte stability
# ---------------------------------------------------------------------------

def test_jcs_output_is_stable():
    """T-JCS-1: Same object produces byte-identical JCS output across calls."""
    obj = {"verdict": "ALLOW", "reasons": ["allowlist_match"]}
    out1 = canonicalise_jcs(obj)
    out2 = canonicalise_jcs(obj)
    assert out1 == out2
    assert isinstance(out1, bytes)


# ---------------------------------------------------------------------------
# T-JCS-2: JCS key-order independence
# ---------------------------------------------------------------------------

def test_jcs_independent_of_insertion_order():
    """T-JCS-2: JCS output is byte-identical regardless of dict insertion order."""
    obj_a = {"z": 1, "a": 2, "m": 3}
    obj_b = {"a": 2, "m": 3, "z": 1}
    assert canonicalise_jcs(obj_a) == canonicalise_jcs(obj_b)


def test_jcs_output_keys_are_sorted():
    """JCS output has lexicographically sorted keys per RFC 8785."""
    obj = {"z": 1, "a": 2}
    decoded = json.loads(canonicalise_jcs(obj).decode("utf-8"))
    assert list(decoded.keys()) == ["a", "z"]


# ---------------------------------------------------------------------------
# T-JCS-3: validate_reason_codes — known codes pass
# ---------------------------------------------------------------------------

def test_validate_known_reason_codes_pass():
    """T-JCS-3: All KNOWN_REASON_CODES pass validation without error."""
    for code in KNOWN_REASON_CODES:
        validate_reason_codes([code])  # must not raise


def test_validate_all_known_codes_together():
    """All four known codes together pass validation."""
    validate_reason_codes(sorted(KNOWN_REASON_CODES))  # must not raise


# ---------------------------------------------------------------------------
# T-JCS-4: validate_reason_codes — unknown code triggers ValueError (fail-closed)
# ---------------------------------------------------------------------------

def test_validate_unknown_reason_code_raises():
    """T-JCS-4: Unknown reason code raises ValueError — fail-closed."""
    with pytest.raises(ValueError, match="unknown reason code"):
        validate_reason_codes(["free_text_reason"])


def test_validate_mixed_known_and_unknown_raises():
    """Mixing known and unknown reason codes still raises."""
    with pytest.raises(ValueError, match="unknown reason code"):
        validate_reason_codes(["allowlist_match", "INJECTED"])


def test_validate_empty_list_passes():
    """Empty reason list passes (no codes to reject)."""
    validate_reason_codes([])  # must not raise


# ---------------------------------------------------------------------------
# T-JCS-5: evaluate() is fail-closed on reason codes
# ---------------------------------------------------------------------------

def test_evaluate_all_verdicts_produce_known_reason_codes():
    """T-JCS-5: All verdict paths produce only known reason codes."""
    # ALLOW
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    for code in v["reasons"]:
        assert code in KNOWN_REASON_CODES, f"Unknown code in ALLOW verdict: {code!r}"

    # REFUSE via denylist
    deny_ruleset = {
        "allowlist": SAMPLE_RULESET["allowlist"],
        "denylist": [{"actor_id": "ricky", "action_class": "FILE", "scope_match": {"project": "alpha"}}],
        "escalation": [],
    }
    v = evaluate(SAMPLE_REQUEST, deny_ruleset)
    for code in v["reasons"]:
        assert code in KNOWN_REASON_CODES, f"Unknown code in REFUSE verdict: {code!r}"

    # ESCALATE
    esc_ruleset = {
        "allowlist": [],
        "denylist": [],
        "escalation": [{"action_class": "FILE", "scope_match": {"project": "alpha"}}],
    }
    v = evaluate(SAMPLE_REQUEST, esc_ruleset)
    for code in v["reasons"]:
        assert code in KNOWN_REASON_CODES, f"Unknown code in ESCALATE verdict: {code!r}"

    # default REFUSE
    v = evaluate(SAMPLE_REQUEST, {"allowlist": [], "denylist": [], "escalation": []})
    for code in v["reasons"]:
        assert code in KNOWN_REASON_CODES, f"Unknown code in default REFUSE verdict: {code!r}"


# ---------------------------------------------------------------------------
# T-JCS-6: report envelope fields
# ---------------------------------------------------------------------------

def test_report_envelope_required_fields():
    """T-JCS-6: Report envelope has all required fields for CI replay."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    required = {"verdict", "reasons", "decision_hash", "request_hash", "artefact_version"}
    assert required.issubset(v.keys()), f"Missing fields: {required - v.keys()}"


def test_report_envelope_verdict_is_string():
    """verdict field is a string (ALLOW/REFUSE/ESCALATE)."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert isinstance(v["verdict"], str)
    assert v["verdict"] in {"ALLOW", "REFUSE", "ESCALATE"}


def test_report_envelope_reasons_is_sorted_list():
    """reasons field is a sorted list of strings."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    assert isinstance(v["reasons"], list)
    assert v["reasons"] == sorted(v["reasons"])


def test_report_envelope_hashes_are_hex():
    """decision_hash and request_hash are lower-case SHA-256 hex strings."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    for field in ("decision_hash", "request_hash"):
        assert len(v[field]) == 64
        assert v[field] == v[field].lower()
        assert all(c in "0123456789abcdef" for c in v[field])


# ---------------------------------------------------------------------------
# T-JCS-7: write_decision_report uses JCS bytes when serialise=canonicalise_jcs
# ---------------------------------------------------------------------------

def test_write_decision_report_jcs_bytes():
    """T-JCS-7: write_decision_report writes JCS bytes when serialise=canonicalise_jcs."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_decision_report(v, v["request_hash"], tmpdir, serialise=canonicalise_jcs)
        written = path.read_bytes()
        expected = canonicalise_jcs(v)
        assert written == expected


def test_write_decision_report_default_uses_canonical():
    """write_decision_report with no serialise defaults to canonicalise()."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = write_decision_report(v, v["request_hash"], tmpdir)
        written = path.read_bytes()
        expected = canonicalise(v)
        assert written == expected


def test_jcs_and_legacy_produce_same_decoded_object():
    """JCS and legacy canonicalize to the same JSON structure."""
    v = evaluate(SAMPLE_REQUEST, SAMPLE_RULESET)
    jcs_decoded = json.loads(canonicalise_jcs(v).decode("utf-8"))
    legacy_decoded = json.loads(canonicalise(v).decode("utf-8"))
    assert jcs_decoded == legacy_decoded
