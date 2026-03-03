# LV/TECH — RUNTIME GOVERNANCE GEOMETRY: TEST MATRIX v0.1

```
artefact_class: NON_EXEC_TEST_SPEC
scope: path validation for LVTECH.RUNTIME_GEOMETRY.v0.1
status: v0.1
```

This matrix describes **allowed and forbidden paths** through the runtime
governance geometry. It is non-executable: a human or CI tool uses it to
verify that an implementation preserves the structural invariants.

---

## 1. VALID PATHS (must be allowed)

| # | Path | Gates traversed | Expected final region | Notes |
|---|------|----------------|----------------------|-------|
| V1 | A -> B -> C | G1 PASS, G2 PASS, G3 PASS, G4 PASS | C | Happy path: full governance, committed |
| V2 | A -> E | G1 FAIL | E | Rejected at admissibility |
| V3 | A -> B -> E | G1 PASS, G2 FAIL | E | Rejected at policy |
| V4 | A -> B -> D | G1 PASS, G2 FAIL (severe) | D | Quarantined at policy |
| V5 | A -> B -> D | G1 PASS, G3 FAIL | D | Quarantined at safety |
| V6 | A -> B -> E | G1 PASS, G3 FAIL | E | Rejected at safety |
| V7 | A -> B -> B | G1 PASS, G4 FAIL | B | Commit denied, stays pending |
| V8 | A -> B -> E | G1 PASS, G4 FAIL | E | Commit denied, rejected |

---

## 2. FORBIDDEN PATHS (must be blocked)

| # | Attempted path | Why forbidden | Expected behaviour |
|---|---------------|---------------|-------------------|
| F1 | A -> C (direct) | Skips all gates | MUST NOT reach C; route to E |
| F2 | B -> C (no G4) | Skips commit gate | MUST NOT cross boundary without G4 PASS |
| F3 | D -> C | Quarantine escape | D is terminal for commit; no path to C |
| F4 | E -> C | Resurrection | E is terminal; no path to C |
| F5 | E -> B | Resurrection | E is terminal; no re-entry to governance |
| F6 | D -> B (without new proposal) | Quarantine escape | D can only re-enter as a new proposal via A |
| F7 | Any -> C (ambiguous gate state) | Indeterminate | FAIL-CLOSED: route to D or E |
| F8 | Any -> C (dependency failure) | Missing input | FAIL-CLOSED: route to D or E |

---

## 3. STRESS SCENARIOS

| # | Scenario | Expected behaviour |
|---|----------|-------------------|
| S1 | Retry cascade (100x G4 FAIL) | Each attempt stays in B or routes to E; never reaches C |
| S2 | Delegation chain (A -> B, delegate to sub-proposal) | Sub-proposal must traverse its own G1-G4; parent cannot inherit child G4 PASS |
| S3 | Tool loop under exhaustion | If gate cannot evaluate, FAIL-CLOSED to D |
| S4 | Partial dependency failure mid-G3 | FAIL-CLOSED: route to D |
| S5 | Policy version drift during evaluation | Gate must use version locked at entry; if version unavailable, FAIL-CLOSED |
| S6 | Runtime attempts to modify enforcement rules | MUST be rejected; Invariant 3 |
| S7 | Commit race (two proposals, same resource) | Each evaluated independently; at most one G4 PASS per resource-state |
| S8 | Post-commit responsibility gap | Evidence record must include authority_id; gap = audit failure |
| S9 | Replay integrity check | Re-running logged inputs through same rule versions must produce same outcome |

---

## 4. PASS CONDITION (for any implementation)

- [ ] No stress case reaches C without G4 PASS.
- [ ] All ambiguity fails downward (to D or E, never to C).
- [ ] Determinism is version-anchored (same inputs + rules = same outcome).
- [ ] Full replay is viable from logs alone.
- [ ] No forbidden path succeeds.
- [ ] All valid paths produce correct final region.

---

**END TEST MATRIX — v0.1**
