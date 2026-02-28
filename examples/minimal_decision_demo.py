"""Minimal MGTP decision artefact demonstration.

Proves:
1. Deterministic canonicalisation: same inputs produce byte-identical output.
2. Stable decision_hash: sha256 of canonical_bytes is invariant.
3. Replayable decision reconstruction.

No randomness. Fixed timestamps. Fixed inputs.
Run with: python examples/minimal_decision_demo.py
"""

import base64
import sys
from pathlib import Path

# Allow running from repo root without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mgtp.types import DecisionRecord

# ---------------------------------------------------------------------------
# Fixed inputs — never change these; they anchor the golden artefact.
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Derive artefact
# ---------------------------------------------------------------------------
canonical = RECORD.canonical_bytes()
b64 = base64.b64encode(canonical).decode("ascii")
h = RECORD.decision_hash()

print("=== MGTP Minimal Decision Artefact ===")
print(f"verdict          : {RECORD.verdict}")
print(f"canonical_bytes  : {b64}")
print(f"decision_hash    : {h}")
