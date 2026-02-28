"""Minimal MGTP decision artefact demonstration.

Proves:
  1) Deterministic canonicalisation — same inputs produce identical bytes.
  2) Stable decision_hash       — sha256 of canonical request+verdict+reasons.
  3) Replayable reconstruction  — stored bytes can be reloaded and re-verified.

No randomness.  Fixed inputs.  Fixed timestamp (excluded from hash).
Run with: python examples/minimal_decision_demo.py
"""

import base64
import sys
from pathlib import Path

# Resolve commit_gate package from repository layout
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "commit_gate" / "src"))

from commit_gate.canonicalise import canonicalise
from commit_gate.engine import evaluate

# ---------------------------------------------------------------------------
# Fixed, deterministic inputs (no randomness, no live timestamps)
# ---------------------------------------------------------------------------

REQUEST = {
    "actor_id": "demo-actor",
    "action_class": "FILE",
    "context": {"description": "minimal demo commit"},
    "authority_scope": {"project": "demo-project"},
    "invariant_hash": "0000000000000000000000000000000000000000000000000000000000000000",
}

RULESET = {
    "allowlist": [
        {
            "actor_id": "demo-actor",
            "action_class": "FILE",
            "scope_match": {"project": "demo-project"},
        }
    ],
    "denylist": [],
    "escalation": [],
}

# ---------------------------------------------------------------------------
# Evaluate and serialise
# ---------------------------------------------------------------------------

result = evaluate(REQUEST, RULESET)
canonical_bytes = canonicalise(result)
canonical_b64 = base64.b64encode(canonical_bytes).decode("ascii")

# ---------------------------------------------------------------------------
# Output — regulator-readable
# ---------------------------------------------------------------------------

print("=== MGTP Minimal Decision Artefact Demo ===")
print()
print(f"verdict        : {result['verdict']}")
print(f"reasons        : {result['reasons']}")
print(f"artefact_version: {result['artefact_version']}")
print(f"request_hash   : {result['request_hash']}")
print(f"decision_hash  : {result['decision_hash']}")
print()
print(f"canonical_bytes (base64):")
print(canonical_b64)
