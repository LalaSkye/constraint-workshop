# Trinity Commit Boundary v1.0

**Classification:** RUNTIME_GOVERNANCE_PRIMITIVE
**Scope:** NON_EXEC_REFERENCE_PACK
**Authority:** HUMAN_ACTUATOR_REQUIRED
**Exit Enum:** {ALLOW, HOLD, DENY, SILENCE}

---

## 0. Purpose

TrinityOS governs the boundary between **EXPLORE** (advisory cognition) and **EXECUTE** (real-world action).

Nothing crosses into EXECUTE without a Trinity verdict.

This is **structural**, not advisory.

---

## 1. Boundary Function

```
INPUT → TRINITY_GATE → VERDICT → (if ALLOW) EXECUTION
```

- If there is **no VERDICT**, there is **no EXECUTION**.
- Only `ALLOW` may cross the boundary.

---

## 2. Commit Payload Schema (trinity.commit.v1)

```json
{
  "schema_version": "trinity.commit.v1",
  "request_id": "string",
  "timestamp_utc": "ISO8601",
  "actor": {
    "actor_type": "HUMAN | SERVICE | AGENT",
    "actor_id": "string",
    "role": "string"
  },
  "intent": {
    "action_type": "string",
    "target": "string",
    "intent_summary": "string"
  },
  "context": {
    "environment": "DEV | STAGE | PROD",
    "domain_id": "string",
    "record_id": "string"
  },
  "authority": {
    "authority_ref": "string",
    "authority_type": "POLICY | CONSENT | CONTRACT | SUPERVISION"
  },
  "risk_mode": "STANDARD | ELEVATED | CRITICAL",
  "constraint_version": "string"
}
```

**Invariants:**
- No hidden fields.
- No implicit inference.
- No interior state.

---

## 3. Exit Enum

| Verdict | Meaning |
|---------|---------|
| **ALLOW** | May cross boundary |
| **HOLD** | Insufficient clarity or authority |
| **DENY** | Explicitly forbidden |
| **SILENCE** | Valid non-response; no propagation |

- `SILENCE` is not failure. It is containment.

---

## 4. Determinism Rules

- Canonical JSON ordering: lexicographic keys.
- Encoding: UTF-8.
- No extraneous whitespace.
- SHA256 over canonical form.
- Artefact hash must validate under replay.
- No probabilistic outcomes.
- Same input → same verdict.

---

## 5. Decision Artefact Schema (trinity.decision.v1)

```json
{
  "schema_version": "trinity.decision.v1",
  "request_id": "string",
  "payload_hash_sha256": "64hex",
  "verdict": "ALLOW | HOLD | DENY | SILENCE",
  "reason_codes": ["string"],
  "constraint_version": "string",
  "evaluated_at_utc": "ISO8601",
  "artefact_hash_sha256": "64hex"
}
```

**"Sealed" means:**
- Canonical form.
- Deterministic hash.
- Replay-verifiable.
- Tamper-detectable.

---

## 6. Fail-Closed Rule

If any of the following hold:
- Required field missing.
- Unknown `constraint_version`.
- Authority undefined.
- Canonicalisation mismatch.

Then:
- Verdict **MUST** be `HOLD` or `DENY`.
- Verdict must **NEVER** be `ALLOW` by default.

---

## 7. Verification Surface (CLI Contract)

```
trinity emit payload.json → decision.json
```
Run Trinity gate and emit sealed decision artefact.

```
trinity verify decision.json → PASS | FAIL
```
Verify canonicalisation + hashes and report integrity.

**Verification checks:**
- Canonical hash integrity.
- Artefact integrity.
- Deterministic re-evaluation (optional in v1.0, required in v1.1).

---

## 8. Non-Claims (v1.0 Scope)

TrinityOS v1.0 does **not** claim:
- Cryptographic signing.
- Hardware binding.
- Kernel-level non-bypassability.
- Blockchain anchoring.
- Regulatory certification.

Claims are bounded to:
- Deterministic boundary gating.
- Tamper-evident artefacts (SHA256 over canonical JSON).
- Fail-closed execution control when correctly wired.

---

## 9. Minimal Runtime Engine (Reference Skeleton)

| Component | Function |
|-----------|----------|
| `canonicalise.py` | Canonical JSON + SHA256 helper |
| `trinity_gate.py` | Gate evaluator (payload → verdict + reason_codes) |
| `emit.py` | Builds `trinity.decision.v1` artefact, attaches `artefact_hash_sha256` |
| `verify.py` | Recomputes canonical form + SHA256, checks `artefact_hash_sha256` |

Plus: golden test fixtures, determinism tests, tamper tests.

---

## 10. Architecture Flow

```
┌─────────────┐
│   INPUT      │  (commit payload: trinity.commit.v1)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ TRINITY_GATE │  (evaluate against constraints)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   VERDICT    │  {ALLOW | HOLD | DENY | SILENCE}
└──────┬──────┘
       │
       ▼ (only if ALLOW)
┌─────────────┐
│  EXECUTION   │  (sealed decision artefact emitted)
└─────────────┘

Fail-closed: no verdict = no execution.
Unknown inputs = HOLD or DENY, never ALLOW.
```

---

## 11. What This Achieves

- A governance boundary specification (this document).
- A commit payload schema (`trinity.commit.v1`).
- A decision artefact schema (`trinity.decision.v1`).
- A verifier surface (`trinity emit` / `trinity verify`).
- An evidence surface independent of any other framework.
