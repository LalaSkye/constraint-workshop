"""Tests for decision_space_ledger — schema validation, canonicalisation, hashing, diff, CLI."""

import json
import sys
import tempfile
from pathlib import Path

# Add src to path so tests can be run from repository root via pytest -q
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from decision_space_ledger import SCHEMA, canonical_hash, canonicalise, diff, validate
from decision_space_ledger.cli import main


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

MINIMAL = {
    "version": "v1",
    "variables": ["A", "B"],
    "allowed_transitions": [{"from": "A", "to": "B"}],
    "exclusions": [],
    "reason_code_families": {},
}

FULL = {
    "version": "v1",
    "variables": ["APPROVE", "DENY", "HOLD", "REVIEW"],
    "allowed_transitions": [
        {"from": "REVIEW", "to": "APPROVE"},
        {"from": "REVIEW", "to": "DENY"},
        {"from": "REVIEW", "to": "HOLD"},
        {"from": "HOLD", "to": "APPROVE"},
        {"from": "HOLD", "to": "DENY"},
    ],
    "exclusions": ["DENY"],
    "reason_code_families": {
        "approval": ["MANUAL", "AUTO"],
        "rejection": ["POLICY_VIOLATION", "TIMEOUT"],
    },
}


def _copy(d):
    return json.loads(json.dumps(d))


# ---------------------------------------------------------------------------
# Schema: SCHEMA constant
# ---------------------------------------------------------------------------

def test_schema_constant_has_required_keys():
    assert SCHEMA["title"] == "decision_space_snapshot_v1"
    assert "properties" in SCHEMA
    required = SCHEMA["required"]
    for key in ("version", "variables", "allowed_transitions", "exclusions", "reason_code_families"):
        assert key in required


# ---------------------------------------------------------------------------
# Validation: valid inputs
# ---------------------------------------------------------------------------

def test_validate_minimal_snapshot():
    result = validate(_copy(MINIMAL))
    assert result["version"] == "v1"


def test_validate_full_snapshot():
    result = validate(_copy(FULL))
    assert result is not None


def test_validate_returns_snapshot_unchanged():
    snap = _copy(MINIMAL)
    result = validate(snap)
    assert result is snap


def test_validate_empty_variables_allowed():
    snap = _copy(MINIMAL)
    snap["variables"] = []
    validate(snap)


def test_validate_empty_transitions_allowed():
    snap = _copy(MINIMAL)
    snap["allowed_transitions"] = []
    validate(snap)


def test_validate_empty_reason_code_families_allowed():
    validate(_copy(MINIMAL))


# ---------------------------------------------------------------------------
# Validation: invalid inputs — top-level
# ---------------------------------------------------------------------------

def test_validate_not_a_dict():
    import pytest
    with pytest.raises(ValueError, match="dict"):
        validate([1, 2, 3])


def test_validate_extra_key_rejected():
    import pytest
    snap = _copy(MINIMAL)
    snap["unexpected_field"] = "oops"
    with pytest.raises(ValueError, match="unexpected keys"):
        validate(snap)


def test_validate_missing_version():
    import pytest
    snap = _copy(MINIMAL)
    del snap["version"]
    with pytest.raises(ValueError, match="version"):
        validate(snap)


def test_validate_missing_variables():
    import pytest
    snap = _copy(MINIMAL)
    del snap["variables"]
    with pytest.raises(ValueError, match="variables"):
        validate(snap)


def test_validate_missing_allowed_transitions():
    import pytest
    snap = _copy(MINIMAL)
    del snap["allowed_transitions"]
    with pytest.raises(ValueError, match="allowed_transitions"):
        validate(snap)


def test_validate_missing_exclusions():
    import pytest
    snap = _copy(MINIMAL)
    del snap["exclusions"]
    with pytest.raises(ValueError, match="exclusions"):
        validate(snap)


def test_validate_missing_reason_code_families():
    import pytest
    snap = _copy(MINIMAL)
    del snap["reason_code_families"]
    with pytest.raises(ValueError, match="reason_code_families"):
        validate(snap)


# ---------------------------------------------------------------------------
# Validation: invalid inputs — version
# ---------------------------------------------------------------------------

def test_validate_wrong_version():
    import pytest
    snap = _copy(MINIMAL)
    snap["version"] = "v2"
    with pytest.raises(ValueError, match="v1"):
        validate(snap)


def test_validate_version_not_string():
    import pytest
    snap = _copy(MINIMAL)
    snap["version"] = 1
    with pytest.raises(ValueError, match="string"):
        validate(snap)


# ---------------------------------------------------------------------------
# Validation: invalid inputs — variables
# ---------------------------------------------------------------------------

def test_validate_variables_not_list():
    import pytest
    snap = _copy(MINIMAL)
    snap["variables"] = "A"
    with pytest.raises(ValueError, match="list"):
        validate(snap)


def test_validate_variables_non_string_item():
    import pytest
    snap = _copy(MINIMAL)
    snap["variables"] = ["A", 42]
    with pytest.raises(ValueError, match="string"):
        validate(snap)


def test_validate_variables_duplicates_rejected():
    import pytest
    snap = _copy(MINIMAL)
    snap["variables"] = ["A", "A"]
    with pytest.raises(ValueError, match="unique"):
        validate(snap)


# ---------------------------------------------------------------------------
# Validation: invalid inputs — allowed_transitions
# ---------------------------------------------------------------------------

def test_validate_transitions_not_list():
    import pytest
    snap = _copy(MINIMAL)
    snap["allowed_transitions"] = "A->B"
    with pytest.raises(ValueError, match="list"):
        validate(snap)


def test_validate_transition_not_dict():
    import pytest
    snap = _copy(MINIMAL)
    snap["allowed_transitions"] = ["A->B"]
    with pytest.raises(ValueError, match="object"):
        validate(snap)


def test_validate_transition_missing_from():
    import pytest
    snap = _copy(MINIMAL)
    snap["allowed_transitions"] = [{"to": "B"}]
    with pytest.raises(ValueError, match="'from'"):
        validate(snap)


def test_validate_transition_missing_to():
    import pytest
    snap = _copy(MINIMAL)
    snap["allowed_transitions"] = [{"from": "A"}]
    with pytest.raises(ValueError, match="'to'"):
        validate(snap)


def test_validate_transition_extra_key_rejected():
    import pytest
    snap = _copy(MINIMAL)
    snap["allowed_transitions"] = [{"from": "A", "to": "B", "weight": 1}]
    with pytest.raises(ValueError, match="unexpected keys"):
        validate(snap)


def test_validate_transition_from_not_string():
    import pytest
    snap = _copy(MINIMAL)
    snap["allowed_transitions"] = [{"from": 0, "to": "B"}]
    with pytest.raises(ValueError, match="string"):
        validate(snap)


# ---------------------------------------------------------------------------
# Validation: invalid inputs — exclusions
# ---------------------------------------------------------------------------

def test_validate_exclusions_not_list():
    import pytest
    snap = _copy(MINIMAL)
    snap["exclusions"] = "X"
    with pytest.raises(ValueError, match="list"):
        validate(snap)


def test_validate_exclusions_non_string_item():
    import pytest
    snap = _copy(MINIMAL)
    snap["exclusions"] = [99]
    with pytest.raises(ValueError, match="string"):
        validate(snap)


def test_validate_exclusions_duplicates_rejected():
    import pytest
    snap = _copy(MINIMAL)
    snap["exclusions"] = ["X", "X"]
    with pytest.raises(ValueError, match="unique"):
        validate(snap)


# ---------------------------------------------------------------------------
# Validation: invalid inputs — reason_code_families
# ---------------------------------------------------------------------------

def test_validate_reason_code_families_not_dict():
    import pytest
    snap = _copy(MINIMAL)
    snap["reason_code_families"] = ["a"]
    with pytest.raises(ValueError, match="object"):
        validate(snap)


def test_validate_reason_code_family_value_not_list():
    import pytest
    snap = _copy(MINIMAL)
    snap["reason_code_families"] = {"approval": "MANUAL"}
    with pytest.raises(ValueError, match="list"):
        validate(snap)


def test_validate_reason_code_family_item_not_string():
    import pytest
    snap = _copy(MINIMAL)
    snap["reason_code_families"] = {"approval": [1, 2]}
    with pytest.raises(ValueError, match="string"):
        validate(snap)


def test_validate_reason_code_family_duplicates_rejected():
    import pytest
    snap = _copy(MINIMAL)
    snap["reason_code_families"] = {"approval": ["MANUAL", "MANUAL"]}
    with pytest.raises(ValueError, match="unique"):
        validate(snap)


# ---------------------------------------------------------------------------
# Canonicalisation
# ---------------------------------------------------------------------------

def test_canonicalise_returns_bytes():
    result = canonicalise(_copy(MINIMAL))
    assert isinstance(result, bytes)


def test_canonicalise_deterministic():
    """Same logical snapshot always produces identical bytes."""
    a = canonicalise(_copy(MINIMAL))
    b = canonicalise(_copy(MINIMAL))
    assert a == b


def test_canonicalise_order_independent_variables():
    """variables are sorted, so insertion order must not matter."""
    snap1 = _copy(MINIMAL)
    snap1["variables"] = ["B", "A"]
    snap2 = _copy(MINIMAL)
    snap2["variables"] = ["A", "B"]
    assert canonicalise(snap1) == canonicalise(snap2)


def test_canonicalise_order_independent_transitions():
    snap1 = _copy(FULL)
    snap2 = _copy(FULL)
    snap2["allowed_transitions"] = list(reversed(snap2["allowed_transitions"]))
    assert canonicalise(snap1) == canonicalise(snap2)


def test_canonicalise_order_independent_exclusions():
    snap1 = _copy(FULL)
    snap1["exclusions"] = ["Y", "X"]
    snap2 = _copy(FULL)
    snap2["exclusions"] = ["X", "Y"]
    assert canonicalise(snap1) == canonicalise(snap2)


def test_canonicalise_order_independent_reason_codes():
    snap1 = _copy(FULL)
    snap1["reason_code_families"]["approval"] = ["AUTO", "MANUAL"]
    snap2 = _copy(FULL)
    snap2["reason_code_families"]["approval"] = ["MANUAL", "AUTO"]
    assert canonicalise(snap1) == canonicalise(snap2)


def test_canonicalise_different_snapshots_differ():
    snap1 = _copy(MINIMAL)
    snap2 = _copy(MINIMAL)
    snap2["variables"] = ["A", "B", "C"]
    assert canonicalise(snap1) != canonicalise(snap2)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def test_hash_is_64_char_hex_lowercase():
    h = canonical_hash(_copy(MINIMAL))
    assert isinstance(h, str)
    assert len(h) == 64
    assert h == h.lower()
    int(h, 16)  # must be valid hex


def test_hash_deterministic():
    h1 = canonical_hash(_copy(MINIMAL))
    h2 = canonical_hash(_copy(MINIMAL))
    assert h1 == h2


def test_hash_order_independent():
    snap1 = _copy(FULL)
    snap2 = _copy(FULL)
    snap2["variables"] = list(reversed(snap2["variables"]))
    assert canonical_hash(snap1) == canonical_hash(snap2)


def test_hash_changes_on_mutation():
    snap1 = _copy(MINIMAL)
    snap2 = _copy(MINIMAL)
    snap2["variables"] = ["Z"]
    assert canonical_hash(snap1) != canonical_hash(snap2)


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def test_diff_identical_snapshots():
    result = diff(_copy(FULL), _copy(FULL))
    assert result["is_identical"] is True
    assert result["variables_added"] == []
    assert result["variables_removed"] == []
    assert result["transitions_added"] == []
    assert result["transitions_removed"] == []
    assert result["exclusions_added"] == []
    assert result["exclusions_removed"] == []
    assert result["reason_code_families_added"] == []
    assert result["reason_code_families_removed"] == []
    assert result["reason_code_families_changed"] == {}


def test_diff_variable_added():
    a = _copy(MINIMAL)
    b = _copy(MINIMAL)
    b["variables"] = ["A", "B", "C"]
    result = diff(a, b)
    assert result["variables_added"] == ["C"]
    assert result["variables_removed"] == []
    assert result["is_identical"] is False


def test_diff_variable_removed():
    a = _copy(FULL)
    b = _copy(FULL)
    b["variables"] = [v for v in b["variables"] if v != "HOLD"]
    result = diff(a, b)
    assert "HOLD" in result["variables_removed"]
    assert result["is_identical"] is False


def test_diff_transition_added():
    a = _copy(MINIMAL)
    b = _copy(MINIMAL)
    b["allowed_transitions"] = [{"from": "A", "to": "B"}, {"from": "B", "to": "A"}]
    result = diff(a, b)
    assert {"from": "B", "to": "A"} in result["transitions_added"]
    assert result["is_identical"] is False


def test_diff_transition_removed():
    a = _copy(FULL)
    b = _copy(FULL)
    b["allowed_transitions"] = [
        t for t in b["allowed_transitions"]
        if not (t["from"] == "HOLD" and t["to"] == "DENY")
    ]
    result = diff(a, b)
    assert {"from": "HOLD", "to": "DENY"} in result["transitions_removed"]


def test_diff_exclusion_added():
    a = _copy(MINIMAL)
    b = _copy(MINIMAL)
    b["exclusions"] = ["X"]
    result = diff(a, b)
    assert result["exclusions_added"] == ["X"]


def test_diff_exclusion_removed():
    a = _copy(FULL)
    b = _copy(FULL)
    b["exclusions"] = []
    result = diff(a, b)
    assert "DENY" in result["exclusions_removed"]


def test_diff_family_added():
    a = _copy(MINIMAL)
    b = _copy(MINIMAL)
    b["reason_code_families"] = {"new_family": ["CODE1"]}
    result = diff(a, b)
    assert "new_family" in result["reason_code_families_added"]
    assert result["is_identical"] is False


def test_diff_family_removed():
    a = _copy(FULL)
    b = _copy(FULL)
    del b["reason_code_families"]["rejection"]
    result = diff(a, b)
    assert "rejection" in result["reason_code_families_removed"]


def test_diff_family_codes_changed():
    a = _copy(FULL)
    b = _copy(FULL)
    b["reason_code_families"]["approval"] = ["MANUAL", "AUTO", "OVERRIDE"]
    result = diff(a, b)
    changed = result["reason_code_families_changed"]
    assert "approval" in changed
    assert "OVERRIDE" in changed["approval"]["codes_added"]
    assert changed["approval"]["codes_removed"] == []


def test_diff_is_deterministic():
    """Running diff twice on the same inputs returns the same result."""
    r1 = diff(_copy(FULL), _copy(MINIMAL))
    r2 = diff(_copy(FULL), _copy(MINIMAL))
    assert r1 == r2


def test_diff_sorted_outputs():
    a = _copy(MINIMAL)
    a["variables"] = []
    b = _copy(MINIMAL)
    b["variables"] = ["C", "A", "B"]
    result = diff(a, b)
    assert result["variables_added"] == sorted(result["variables_added"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _write_json(path, obj):
    Path(path).write_text(json.dumps(obj), encoding="utf-8")


def test_cli_compare_identical(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        a_path = str(Path(tmp) / "a.json")
        b_path = str(Path(tmp) / "b.json")
        _write_json(a_path, _copy(FULL))
        _write_json(b_path, _copy(FULL))
        rc = main([a_path, b_path])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["diff"]["is_identical"] is True
        assert len(out["snapshot_a"]["hash"]) == 64
        assert out["snapshot_a"]["hash"] == out["snapshot_b"]["hash"]


def test_cli_compare_different(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        a_path = str(Path(tmp) / "a.json")
        b_path = str(Path(tmp) / "b.json")
        _write_json(a_path, _copy(MINIMAL))
        b = _copy(FULL)
        _write_json(b_path, b)
        rc = main([a_path, b_path])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["diff"]["is_identical"] is False
        assert out["snapshot_a"]["hash"] != out["snapshot_b"]["hash"]


def test_cli_no_args(capsys):
    rc = main([])
    assert rc == 2


def test_cli_one_arg(capsys):
    rc = main(["only_one.json"])
    assert rc == 2


def test_cli_invalid_json(capsys, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    good = tmp_path / "good.json"
    _write_json(str(good), _copy(MINIMAL))
    rc = main([str(bad), str(good)])
    assert rc == 1


def test_cli_invalid_snapshot(capsys, tmp_path):
    invalid = tmp_path / "invalid.json"
    _write_json(str(invalid), {"version": "v2"})
    good = tmp_path / "good.json"
    _write_json(str(good), _copy(MINIMAL))
    rc = main([str(invalid), str(good)])
    assert rc == 1


def test_cli_missing_file(capsys):
    rc = main(["/nonexistent/a.json", "/nonexistent/b.json"])
    assert rc == 1
