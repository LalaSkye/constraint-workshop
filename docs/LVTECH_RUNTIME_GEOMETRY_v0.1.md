# LV/TECH — RUNTIME GOVERNANCE GEOMETRY v0.1

```
artefact_class: NON_EXEC_SPEC
scope: single-canonical-build
status: v0.1 (foundational)
purpose: Inspectable runtime governance geometry defining binding,
         commit control, and failure guarantees
```

---

## I. SCOPE

This artefact defines a runtime governance geometry for systems that must
bind authority prior to irreversible execution.

It specifies:

- State-space regions
- A singular commit boundary
- Deterministic gate semantics
- Failure posture guarantees
- Evidence and inspectability requirements
- Canonical diagram layout

Model-agnostic. Implementation-neutral. Non-executing.

---

## II. STATE-SPACE REGIONS (DISJOINT)

| Region | Name | Description |
|--------|------|-------------|
| **A** | UNCONTROLLED | Inputs/events not yet bound to governance. |
| **B** | GOVERNED_PENDING | Under governance evaluation. No durable system-of-record effect. |
| **C** | COMMITTED | Durable effect applied to system-of-record. |
| **D** | QUARANTINED | Blocked/held for investigation. No commit allowed. |
| **E** | REJECTED | Discarded. No side-effects. |

Regions are mutually exclusive. No implicit transitions exist.

---

## III. COMMIT BOUNDARY

`COMMIT_BOUNDARY` separates B from C.

Properties:

- Crossing is only possible via **G4 (Commit Gate) PASS**.
- Boundary is **one-way**.
- Rollback is modelled as a **new governed proposal**, not reversal of history.
- No bypass path to C exists by design.

> This boundary is the enforcement surface.

---

## IV. DETERMINISTIC GATES

Closed outcome set: `PASS | FAIL`

All gates are replayable:
**Same logged inputs + same rule versions = same outcome.**

### G1 — ADMISSIBILITY

- `A -> B` (PASS)
- `A -> E` (FAIL)

### G2 — POLICY

- `B -> continue in B` (PASS)
- `B -> E or D` (FAIL; severity explicit)

### G3 — SAFETY

- `B -> eligible for commit` (PASS)
- `B -> D or E` (FAIL)

### G4 — COMMIT

- `B -> C` (PASS; cross COMMIT_BOUNDARY)
- `B -> remain in B or -> E` (FAIL; never cross)

**No other transition reaches C.**

---

## V. FAILURE POSTURE

Default: **FAIL-CLOSED** for all gates impacting commit.

Guarantees:

- No trajectory reaches C without logged G4 PASS.
- Ambiguity, dependency failure, or indeterminate state routes to D or E.
- Downstream failure cannot retroactively alter boundary rules.
- Read-only flows (if configured) cannot cross COMMIT_BOUNDARY.

> Failure containment is structural, not advisory.

---

## VI. EVIDENCE & INSPECTABILITY

Each transition emits a decision artefact:

| Field | Description |
|-------|-------------|
| `trace_id` | Unique identifier for this proposal trajectory |
| `prior_region` | Region before transition |
| `next_region` | Region after transition |
| `gate_id` | G1-G4 |
| `input_snapshot_refs` | References to inputs at decision time |
| `rule_identifiers` | Rule IDs + versions applied |
| `authority_id` | Who/what authorised this transition |
| `outcome` | PASS or FAIL |
| `reason_code` | Enumerated reason |
| `timestamp` | When the transition occurred |

Audit conditions:

- Full trajectory reconstructible from logs alone.
- Gate outcomes replayable.
- **No-bypass verifiable**: no entry into C without corresponding G4 PASS.

---

## VII. CANONICAL DIAGRAM (REFERENCE LAYOUT)

Flow direction:
- Left to Right = increasing irreversibility
- Top to Bottom = increasing containment

```
+---------------------+
| A: UNCONTROLLED     |
+---------------------+
          |
          | G1 PASS
          v
+---------------------------+
| B: GOVERNED_PENDING       |
+---------------------------+
     |              |
     | G2 FAIL      | G3 FAIL
     v              v
+--------------+  +----------------+
| E: REJECTED  |  | D: QUARANTINED |
+--------------+  +----------------+
          |
          | G4 PASS
          v
||=====================||
||  COMMIT_BOUNDARY    ||
||=====================||
          |
          v
+---------------------+
| C: COMMITTED        |
+---------------------+
```

Diagram rules:

- Only G4 PASS crosses COMMIT_BOUNDARY.
- No diagonal or implicit transitions.
- Failure routes downward, never forward.
- Boundary is visually heavier than other lines.

---

## VIII. STRUCTURAL INVARIANTS

| # | Invariant |
|---|----------|
| 1 | No path to C without G4 PASS. |
| 2 | All FAIL outcomes route to {B, D, E}. |
| 3 | Enforcement rules are externally versioned; runtime cannot self-modify them. |
| 4 | Evidence alone is sufficient for full replay. |

---

**END ARTEFACT — v0.1**
