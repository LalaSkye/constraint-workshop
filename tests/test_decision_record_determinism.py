"""Tests for DecisionRecord: determinism, golden replay, time-bound, evidence, surface-area guard."""

import base64
import hashlib
import json
from pathlib import Path

from mgtp.decision_record import (
    EVIDENCE_MISSING_REASON,
    OUTSIDE_WINDOW_REASON,
    DecisionRecord,
    evaluate,
)
from mgtp.types import EvidenceRef

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "golden_decision.json"

_GOLDEN_RECORD = DecisionRecord(
    record_id="rec-golden-001",
    decision_time="2026-02-28T12:00:00Z",
    authority_window_start="2026-02-28T00:00:00Z",
    authority_window_end="2026-02-28T23:59:59Z",
    verdict="ALLOW",
    reason_codes=("allowlist_match",),
    provided_evidence=(EvidenceRef(ref_id="ev-001", description="owner confirmed"),),
)


# ---------------------------------------------------------------------------
# 1. Determinism: N=50 identical calls must yield identical bytes and hash
# ---------------------------------------------------------------------------

def test_canonical_bytes_determinism_n50():
    """canonical_bytes() is byte-identical across 50 calls."""
    first = _GOLDEN_RECORD.canonical_bytes()
    for _ in range(49):
        assert _GOLDEN_RECORD.canonical_bytes() == first, "canonical_bytes() not deterministic"


def test_decision_hash_determinism_n50():
    """decision_hash is identical across 50 calls."""
    first = _GOLDEN_RECORD.decision_hash
    for _ in range(49):
        assert _GOLDEN_RECORD.decision_hash == first, "decision_hash not deterministic"
    assert first == first.lower(), "decision_hash must be lowercase hex"
    assert len(first) == 64, "decision_hash must be 64-char sha256 hex"


# ---------------------------------------------------------------------------
# 2. Cross-process reproducibility: match stored golden fixture
# ---------------------------------------------------------------------------

def test_golden_replay():
    """Canonical bytes and hash match the stored golden fixture."""
    fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    canonical = _GOLDEN_RECORD.canonical_bytes()
    assert base64.b64encode(canonical).decode() == fixture["golden_canonical_b64"], (
        "canonical_bytes() does not match golden fixture"
    )
    assert _GOLDEN_RECORD.decision_hash == fixture["golden_hash"], (
        "decision_hash does not match golden fixture"
    )


# ---------------------------------------------------------------------------
# 3. Time-bound enforcement
# ---------------------------------------------------------------------------

def test_decision_time_before_window_refused():
    """decision_time before window_start => verdict REFUSE."""
    rec = evaluate(
        record_id="rec-tb-001",
        decision_time="2026-02-27T23:59:59Z",  # 1 second before window
        authority_window_start="2026-02-28T00:00:00Z",
        authority_window_end="2026-02-28T23:59:59Z",
        requested_verdict="ALLOW",
        reason_codes=["allowlist_match"],
        provided_evidence=[EvidenceRef(ref_id="ev-001", description="owner confirmed")],
    )
    assert rec.verdict == "REFUSE"
    assert OUTSIDE_WINDOW_REASON in rec.reason_codes


def test_decision_time_after_window_refused():
    """decision_time after window_end => verdict REFUSE."""
    rec = evaluate(
        record_id="rec-tb-002",
        decision_time="2026-03-01T00:00:00Z",  # 1 day after window
        authority_window_start="2026-02-28T00:00:00Z",
        authority_window_end="2026-02-28T23:59:59Z",
        requested_verdict="ALLOW",
        reason_codes=["allowlist_match"],
        provided_evidence=[EvidenceRef(ref_id="ev-001", description="owner confirmed")],
    )
    assert rec.verdict == "REFUSE"
    assert OUTSIDE_WINDOW_REASON in rec.reason_codes


def test_decision_time_inside_window_accepted():
    """decision_time inside window leaves verdict unchanged."""
    rec = evaluate(
        record_id="rec-tb-003",
        decision_time="2026-02-28T12:00:00Z",
        authority_window_start="2026-02-28T00:00:00Z",
        authority_window_end="2026-02-28T23:59:59Z",
        requested_verdict="ALLOW",
        reason_codes=["allowlist_match"],
        provided_evidence=[EvidenceRef(ref_id="ev-001", description="owner confirmed")],
    )
    assert rec.verdict == "ALLOW"
    assert OUTSIDE_WINDOW_REASON not in rec.reason_codes


# ---------------------------------------------------------------------------
# 4. Evidence enforcement (fail-closed)
# ---------------------------------------------------------------------------

def test_allow_without_evidence_fails_closed():
    """ALLOW with provided_evidence=None => REFUSE with evidence_missing reason."""
    rec = evaluate(
        record_id="rec-ev-001",
        decision_time="2026-02-28T12:00:00Z",
        authority_window_start="2026-02-28T00:00:00Z",
        authority_window_end="2026-02-28T23:59:59Z",
        requested_verdict="ALLOW",
        reason_codes=["allowlist_match"],
        provided_evidence=None,
    )
    assert rec.verdict == "REFUSE"
    assert EVIDENCE_MISSING_REASON in rec.reason_codes


def test_refuse_without_evidence_allowed():
    """REFUSE verdict does not require evidence; no evidence_missing injected."""
    rec = evaluate(
        record_id="rec-ev-002",
        decision_time="2026-02-28T12:00:00Z",
        authority_window_start="2026-02-28T00:00:00Z",
        authority_window_end="2026-02-28T23:59:59Z",
        requested_verdict="REFUSE",
        reason_codes=["denylist_match"],
        provided_evidence=None,
    )
    assert rec.verdict == "REFUSE"
    assert EVIDENCE_MISSING_REASON not in rec.reason_codes


def test_supervised_without_evidence_allowed():
    """SUPERVISED verdict does not require evidence."""
    rec = evaluate(
        record_id="rec-ev-003",
        decision_time="2026-02-28T12:00:00Z",
        authority_window_start="2026-02-28T00:00:00Z",
        authority_window_end="2026-02-28T23:59:59Z",
        requested_verdict="SUPERVISED",
        reason_codes=["escalation_match"],
        provided_evidence=None,
    )
    assert rec.verdict == "SUPERVISED"
    assert EVIDENCE_MISSING_REASON not in rec.reason_codes


# ---------------------------------------------------------------------------
# 5. Surface-area guard: forbidden files must not be modified
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent

_FORBIDDEN_HASHES = {
    "authority_gate.py": "78975c58f28c95bdb111f787b8edec58c2bdbdd132e2ea7c8e7b7c1e8e67e6f5",
    "stop_machine.py":   "473da80d555daf7883bfbe84a24c54660e9f844a6fa8d11d1f9ce68e91a41c5c",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_surface_area_guard_authority_gate():
    """authority_gate.py must not be modified (hash guard)."""
    path = _REPO_ROOT / "authority_gate.py"
    assert path.exists(), "authority_gate.py missing"
    assert _sha256_file(path) == _FORBIDDEN_HASHES["authority_gate.py"], (
        "authority_gate.py has been modified – revert it"
    )


def test_surface_area_guard_stop_machine():
    """stop_machine.py must not be modified (hash guard)."""
    path = _REPO_ROOT / "stop_machine.py"
    assert path.exists(), "stop_machine.py missing"
    assert _sha256_file(path) == _FORBIDDEN_HASHES["stop_machine.py"], (
        "stop_machine.py has been modified – revert it"
    )


def test_surface_area_guard_commit_gate_dir():
    """commit_gate/ directory must not be modified (hash guard on each .py file)."""
    _COMMIT_GATE_HASHES = {
        "commit_gate/tests/test_drift.py":
            "df741d98527925a4b2c581c6ee60ca648e8584b3a46fb64cc3cc77fc20605221",
        "commit_gate/tests/test_determinism.py":
            "b3538e34e6d14778fc5c5250b4f8cd8857cac093e0ff10fa76edb0bab8e09f87",
        "commit_gate/src/commit_gate/canonicalise.py":
            "69c5e87b7492dd9083f2a309c55d46fa96d47ff67ab019e56b53ad9b3d65ba67",
        "commit_gate/src/commit_gate/__init__.py":
            "11c733509357bd55131ab6a33a9f3324bcd540ad470ef203ceb58ac81b5d92ff",
        "commit_gate/src/commit_gate/cli.py":
            "34a06af33216d8190f3df691f0bdae43567f2356f60f942c0b0c0e18cb88a55f",
        "commit_gate/src/commit_gate/engine.py":
            "0c3849e4843aa0ae3bbfbe49c738e969ab2f48d4a00c8745173ec362fc600011",
        "commit_gate/src/commit_gate/drift.py":
            "9e4da9eda0cd74a9a9542a14417d098af82abd06d88c8173970d98fbf4c3ebfb",
        "commit_gate/src/commit_gate/__main__.py":
            "f5bd098fa98ac8da4a5090aaeec471f40b82fbb0ec399922416f6301c681f88c",
    }
    for rel, expected_hash in _COMMIT_GATE_HASHES.items():
        path = _REPO_ROOT / rel
        assert path.exists(), f"{rel} missing from commit_gate"
        assert _sha256_file(path) == expected_hash, (
            f"{rel} has been modified – revert it"
        )
