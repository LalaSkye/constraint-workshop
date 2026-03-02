"""Tests for mgtp.decision_space — Decision-Space Diff Ledger."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mgtp.decision_space import (
    KNOWN_REASON_FAMILIES,
    SCHEMA_VERSION,
    build_diff_report,
    canonicalize_snapshot,
    diff_snapshots,
    snapshot_hash,
    validate_snapshot,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_SNAPSHOT = {
    "version": "v1",
    "variables": ["x", "y", "z"],
    "allowed_transitions": [
        {"from": "GREEN", "to": "AMBER"},
        {"from": "AMBER", "to": "RED"},
    ],
    "exclusions": ["deprecated_var"],
    "reason_code_families": {
        "ALLOW": ["allowlist_match"],
        "REFUSE": ["default_refuse", "denylist_match"],
    },
}

VALID_SNAPSHOT_B = {
    "version": "v1",
    "variables": ["x", "y", "z", "w"],
    "allowed_transitions": [
        {"from": "AMBER", "to": "RED"},
        {"from": "GREEN", "to": "AMBER"},
        {"from": "GREEN", "to": "RED"},
    ],
    "exclusions": [],
    "reason_code_families": {
        "ALLOW": ["allowlist_match", "escalation_override"],
        "REFUSE": ["default_refuse"],
    },
}


# ---------------------------------------------------------------------------
# validate_snapshot — valid cases
# ---------------------------------------------------------------------------

def test_valid_snapshot_passes():
    validate_snapshot(VALID_SNAPSHOT)  # must not raise


def test_valid_empty_lists():
    snap = {
        "version": "v1",
        "variables": [],
        "allowed_transitions": [],
        "exclusions": [],
        "reason_code_families": {},
    }
    validate_snapshot(snap)  # must not raise


# ---------------------------------------------------------------------------
# validate_snapshot — schema violation cases
# ---------------------------------------------------------------------------

def test_non_dict_raises():
    with pytest.raises(ValueError, match="must be a dict"):
        validate_snapshot(["not", "a", "dict"])


def test_missing_version_raises():
    snap = dict(VALID_SNAPSHOT)
    del snap["version"]
    with pytest.raises(ValueError, match="version"):
        validate_snapshot(snap)


def test_wrong_version_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["version"] = "v2"
    with pytest.raises(ValueError, match="unsupported version"):
        validate_snapshot(snap)


def test_missing_variables_raises():
    snap = {k: v for k, v in VALID_SNAPSHOT.items() if k != "variables"}
    with pytest.raises(ValueError, match="variables"):
        validate_snapshot(snap)


def test_variables_not_list_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["variables"] = "not_a_list"
    with pytest.raises(ValueError, match="variables must be a list"):
        validate_snapshot(snap)


def test_variables_non_string_element_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["variables"] = ["ok", 42]
    with pytest.raises(ValueError, match="variables\\[1\\]"):
        validate_snapshot(snap)


def test_missing_allowed_transitions_raises():
    snap = {k: v for k, v in VALID_SNAPSHOT.items() if k != "allowed_transitions"}
    with pytest.raises(ValueError, match="allowed_transitions"):
        validate_snapshot(snap)


def test_allowed_transitions_not_list_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["allowed_transitions"] = {"from": "A", "to": "B"}
    with pytest.raises(ValueError, match="allowed_transitions must be a list"):
        validate_snapshot(snap)


def test_transition_missing_from_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["allowed_transitions"] = [{"to": "AMBER"}]
    with pytest.raises(ValueError, match="from"):
        validate_snapshot(snap)


def test_transition_missing_to_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["allowed_transitions"] = [{"from": "GREEN"}]
    with pytest.raises(ValueError, match="to"):
        validate_snapshot(snap)


def test_transition_from_non_string_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["allowed_transitions"] = [{"from": 1, "to": "AMBER"}]
    with pytest.raises(ValueError, match="from must be a string"):
        validate_snapshot(snap)


def test_transition_to_non_string_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["allowed_transitions"] = [{"from": "GREEN", "to": 2}]
    with pytest.raises(ValueError, match="to must be a string"):
        validate_snapshot(snap)


def test_missing_exclusions_raises():
    snap = {k: v for k, v in VALID_SNAPSHOT.items() if k != "exclusions"}
    with pytest.raises(ValueError, match="exclusions"):
        validate_snapshot(snap)


def test_exclusions_not_list_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["exclusions"] = "bad"
    with pytest.raises(ValueError, match="exclusions must be a list"):
        validate_snapshot(snap)


def test_exclusions_non_string_element_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["exclusions"] = [True]
    with pytest.raises(ValueError, match="exclusions\\[0\\]"):
        validate_snapshot(snap)


def test_missing_reason_code_families_raises():
    snap = {k: v for k, v in VALID_SNAPSHOT.items() if k != "reason_code_families"}
    with pytest.raises(ValueError, match="reason_code_families"):
        validate_snapshot(snap)


def test_reason_code_families_not_dict_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["reason_code_families"] = ["ALLOW"]
    with pytest.raises(ValueError, match="reason_code_families must be a dict"):
        validate_snapshot(snap)


def test_reason_code_family_value_not_list_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["reason_code_families"] = {"ALLOW": "not_a_list"}
    with pytest.raises(ValueError, match="must be a list"):
        validate_snapshot(snap)


def test_reason_code_family_code_non_string_raises():
    snap = dict(VALID_SNAPSHOT)
    snap["reason_code_families"] = {"ALLOW": [99]}
    with pytest.raises(ValueError, match="must be a string"):
        validate_snapshot(snap)


# ---------------------------------------------------------------------------
# canonicalize_snapshot
# ---------------------------------------------------------------------------

def test_canonicalize_sorts_variables():
    snap = dict(VALID_SNAPSHOT)
    snap["variables"] = ["z", "a", "m"]
    result = canonicalize_snapshot(snap)
    assert result["variables"] == ["a", "m", "z"]


def test_canonicalize_sorts_exclusions():
    snap = dict(VALID_SNAPSHOT)
    snap["exclusions"] = ["gamma", "alpha", "beta"]
    result = canonicalize_snapshot(snap)
    assert result["exclusions"] == ["alpha", "beta", "gamma"]


def test_canonicalize_sorts_transitions():
    snap = dict(VALID_SNAPSHOT)
    snap["allowed_transitions"] = [
        {"from": "RED", "to": "GREEN"},
        {"from": "AMBER", "to": "RED"},
        {"from": "GREEN", "to": "AMBER"},
    ]
    result = canonicalize_snapshot(snap)
    assert result["allowed_transitions"] == [
        {"from": "AMBER", "to": "RED"},
        {"from": "GREEN", "to": "AMBER"},
        {"from": "RED", "to": "GREEN"},
    ]


def test_canonicalize_sorts_reason_code_families_keys():
    snap = dict(VALID_SNAPSHOT)
    snap["reason_code_families"] = {"Z_FAM": ["z_code"], "A_FAM": ["a_code"]}
    result = canonicalize_snapshot(snap)
    assert list(result["reason_code_families"].keys()) == ["A_FAM", "Z_FAM"]


def test_canonicalize_sorts_reason_codes_within_family():
    snap = dict(VALID_SNAPSHOT)
    snap["reason_code_families"] = {"ALLOW": ["z_code", "a_code", "m_code"]}
    result = canonicalize_snapshot(snap)
    assert result["reason_code_families"]["ALLOW"] == ["a_code", "m_code", "z_code"]


# ---------------------------------------------------------------------------
# snapshot_hash — stability and determinism
# ---------------------------------------------------------------------------

def test_hash_is_stable():
    h1 = snapshot_hash(VALID_SNAPSHOT)
    h2 = snapshot_hash(VALID_SNAPSHOT)
    assert h1 == h2


def test_hash_is_lowercase_hex():
    h = snapshot_hash(VALID_SNAPSHOT)
    assert len(h) == 64
    assert h == h.lower()
    assert all(c in "0123456789abcdef" for c in h)


def test_hash_independent_of_key_insertion_order():
    snap_a = {
        "version": "v1",
        "variables": ["x"],
        "allowed_transitions": [],
        "exclusions": [],
        "reason_code_families": {},
    }
    snap_b = {
        "exclusions": [],
        "allowed_transitions": [],
        "reason_code_families": {},
        "variables": ["x"],
        "version": "v1",
    }
    assert snapshot_hash(snap_a) == snapshot_hash(snap_b)


def test_hash_independent_of_list_order():
    snap_a = dict(VALID_SNAPSHOT)
    snap_a["variables"] = ["z", "y", "x"]
    snap_b = dict(VALID_SNAPSHOT)
    snap_b["variables"] = ["x", "y", "z"]
    assert snapshot_hash(snap_a) == snapshot_hash(snap_b)


def test_different_snapshots_have_different_hashes():
    assert snapshot_hash(VALID_SNAPSHOT) != snapshot_hash(VALID_SNAPSHOT_B)


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_identical_snapshots_produce_empty_diff():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT)
    assert diff["variables_added"] == []
    assert diff["variables_removed"] == []
    assert diff["transitions_added"] == []
    assert diff["transitions_removed"] == []
    assert diff["exclusions_added"] == []
    assert diff["exclusions_removed"] == []
    assert diff["reason_codes_added"] == {}
    assert diff["reason_codes_removed"] == {}


def test_diff_detects_variable_added():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert "w" in diff["variables_added"]


def test_diff_detects_no_variable_removed_when_b_is_superset():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    # VALID_SNAPSHOT_B adds "w" but keeps x, y, z
    assert diff["variables_removed"] == []


def test_diff_detects_variable_removed():
    diff = diff_snapshots(VALID_SNAPSHOT_B, VALID_SNAPSHOT)
    assert "w" in diff["variables_removed"]


def test_diff_detects_transition_added():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert {"from": "GREEN", "to": "RED"} in diff["transitions_added"]


def test_diff_detects_transition_removed():
    diff = diff_snapshots(VALID_SNAPSHOT_B, VALID_SNAPSHOT)
    assert {"from": "GREEN", "to": "RED"} in diff["transitions_removed"]


def test_diff_detects_exclusion_removed():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert "deprecated_var" in diff["exclusions_removed"]


def test_diff_detects_exclusion_added():
    diff = diff_snapshots(VALID_SNAPSHOT_B, VALID_SNAPSHOT)
    assert "deprecated_var" in diff["exclusions_added"]


def test_diff_detects_reason_code_added():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert "escalation_override" in diff["reason_codes_added"].get("ALLOW", [])


def test_diff_detects_reason_code_removed():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert "denylist_match" in diff["reason_codes_removed"].get("REFUSE", [])


def test_diff_raises_on_invalid_snapshot_a():
    bad = {"version": "v1"}
    with pytest.raises(ValueError):
        diff_snapshots(bad, VALID_SNAPSHOT)


def test_diff_raises_on_invalid_snapshot_b():
    bad = {"version": "v1"}
    with pytest.raises(ValueError):
        diff_snapshots(VALID_SNAPSHOT, bad)


def test_diff_is_deterministic():
    d1 = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    d2 = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


def test_diff_no_false_positives_for_unchanged_items():
    snap_a = {
        "version": "v1",
        "variables": ["x", "y"],
        "allowed_transitions": [{"from": "A", "to": "B"}],
        "exclusions": ["ex1"],
        "reason_code_families": {"ALLOW": ["allowlist_match"]},
    }
    snap_b = dict(snap_a)
    snap_b["variables"] = ["x", "y", "z"]  # only add z
    diff = diff_snapshots(snap_a, snap_b)
    assert diff["variables_added"] == ["z"]
    assert diff["variables_removed"] == []
    assert diff["transitions_added"] == []
    assert diff["transitions_removed"] == []
    assert diff["exclusions_added"] == []
    assert diff["exclusions_removed"] == []
    assert diff["reason_codes_added"] == {}
    assert diff["reason_codes_removed"] == {}


def test_diff_output_keys_present():
    diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    expected_keys = {
        "variables_added",
        "variables_removed",
        "transitions_added",
        "transitions_removed",
        "exclusions_added",
        "exclusions_removed",
        "reason_codes_added",
        "reason_codes_removed",
    }
    assert set(diff.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Constants — SCHEMA_VERSION and KNOWN_REASON_FAMILIES
# ---------------------------------------------------------------------------

def test_schema_version_value():
    assert SCHEMA_VERSION == "v1"


def test_known_reason_families_contains_required():
    assert "ALLOW" in KNOWN_REASON_FAMILIES
    assert "REFUSE" in KNOWN_REASON_FAMILIES
    assert "ESCALATE" in KNOWN_REASON_FAMILIES


def test_known_reason_families_is_frozenset():
    assert isinstance(KNOWN_REASON_FAMILIES, frozenset)


def test_unknown_family_name_rejected_by_validate():
    snap = dict(VALID_SNAPSHOT)
    snap["reason_code_families"] = {"UNKNOWN_FAM": ["some_code"]}
    with pytest.raises(ValueError, match="unknown reason_code_families key"):
        validate_snapshot(snap)


def test_known_family_names_accepted_by_validate():
    snap = {
        "version": "v1",
        "variables": ["x"],
        "allowed_transitions": [],
        "exclusions": [],
        "reason_code_families": {
            "ALLOW": ["allowlist_match"],
            "REFUSE": ["default_refuse"],
            "ESCALATE": ["escalation_match"],
        },
    }
    validate_snapshot(snap)  # must not raise


# ---------------------------------------------------------------------------
# build_diff_report — PASS/FAIL CI replay envelope
# ---------------------------------------------------------------------------

def test_diff_report_pass_for_identical_snapshots():
    report = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT)
    assert report["status"] == "PASS"


def test_diff_report_fail_for_different_snapshots():
    report = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert report["status"] == "FAIL"


def test_diff_report_schema_version():
    report = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT)
    assert report["schema_version"] == SCHEMA_VERSION


def test_diff_report_envelope_keys():
    report = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert set(report.keys()) == {
        "schema_version", "status", "snapshot_a_hash", "snapshot_b_hash", "diff",
    }


def test_diff_report_hashes_match_snapshot_hash():
    report = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert report["snapshot_a_hash"] == snapshot_hash(VALID_SNAPSHOT)
    assert report["snapshot_b_hash"] == snapshot_hash(VALID_SNAPSHOT_B)


def test_diff_report_is_deterministic():
    r1 = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    r2 = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_diff_report_diff_matches_diff_snapshots():
    report = build_diff_report(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    expected_diff = diff_snapshots(VALID_SNAPSHOT, VALID_SNAPSHOT_B)
    assert report["diff"] == expected_diff


def test_diff_report_raises_on_invalid_snapshot():
    bad = {"version": "v1"}
    with pytest.raises(ValueError):
        build_diff_report(bad, VALID_SNAPSHOT)
