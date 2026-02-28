"""Replay test: golden canonical bytes → decision_hash round-trip.

Proves:
- Same inputs produce byte-identical canonical_bytes (replay works).
- decision_hash computed from stored bytes equals decision_hash from live record.
- Any byte-level drift in DecisionRecord serialisation fails this test.
"""

import base64
import hashlib
from pathlib import Path

from mgtp.types import DecisionRecord

GOLDEN_B64_PATH = Path(__file__).parent / "golden" / "decision_golden.b64"

# Fixed inputs — must match examples/minimal_decision_demo.py exactly.
RECORD = DecisionRecord(
    transition_id="txn-0001",
    risk_class="LOW",
    irreversible=False,
    resource_identifier="res://demo/alpha",
    trust_boundary_crossed=False,
    override_token=None,
    timestamp="2026-01-01T00:00:00Z",
    actor_id="demo-actor",
    authority_basis="OWNER",
    tenant_id="tenant-001",
    verdict="APPROVED",
)


def _load_golden_bytes() -> bytes:
    b64 = GOLDEN_B64_PATH.read_text(encoding="ascii").strip()
    return base64.b64decode(b64)


def test_canonical_bytes_match_golden():
    """Live canonical_bytes must be byte-identical to stored golden fixture."""
    golden = _load_golden_bytes()
    live = RECORD.canonical_bytes()
    assert live == golden, (
        f"canonical_bytes drift detected.\n"
        f"  expected : {golden!r}\n"
        f"  got      : {live!r}"
    )


def test_decision_hash_stable():
    """decision_hash is sha256 of canonical_bytes — must equal golden hash."""
    golden = _load_golden_bytes()
    expected_hash = hashlib.sha256(golden).hexdigest()
    assert RECORD.decision_hash() == expected_hash


def test_decision_hash_replay():
    """Recomputing decision_hash from stored bytes equals live decision_hash."""
    stored_bytes = _load_golden_bytes()
    replayed_hash = hashlib.sha256(stored_bytes).hexdigest()
    live_hash = RECORD.decision_hash()
    assert replayed_hash == live_hash, (
        f"Replay hash mismatch.\n"
        f"  replayed : {replayed_hash}\n"
        f"  live     : {live_hash}"
    )
