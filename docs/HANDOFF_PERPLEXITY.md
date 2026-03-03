# HANDOFF: LV/TECH — RUNTIME GOVERNANCE GEOMETRY (v0.1)

Instructions for any AI assistant (Perplexity, Copilot, Claude, etc.)
working in this repository.

---

## 0. Operating constraints

You are acting as a **repo-local builder** for this project.

You MUST treat this artefact as the **single source of truth**:

- `ARTEFACT_ID`: `LVTECH.RUNTIME_GEOMETRY.v0.1`
- `ARTEFACT_CLASS`: `NON_EXEC_SPEC` + `NON_EXEC_TEST_SPEC`
- `SCOPE`: runtime governance geometry (regions, gates, boundary, evidence)
- `STATUS`: `COMPLETE_v0.1`
- `EXECUTION`: You MAY propose files, code, and tests. The HUMAN decides what to run.

You MUST NOT:

- Change the meaning of regions A/B/C/D/E.
- Change the meaning of gates G1–G4, their PASS/FAIL outcomes, or commit boundary semantics.
- Introduce new regions or gates without an explicit new spec version.
- Remove or weaken any structural invariant in the spec.

All design and code you propose MUST preserve the invariants documented in:

- `docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md` (Sections III–IV, VIII)

---

## 1. What is fixed (not up for debate)

### Regions (disjoint)

| Region | Name | Meaning |
|--------|------|---------|
| A | UNCONTROLLED | Pre-governance inputs/events |
| B | GOVERNED_PENDING | Under evaluation, no system-of-record effect |
| C | COMMITTED | Durable effect applied |
| D | QUARANTINED | Blocked/held, no commit |
| E | REJECTED | Discarded, no side-effects |

### Commit boundary

- Separates B from C. One-way. Only via G4 PASS.
- Rollback = new governed proposal, not reversal.

### Deterministic gates

- G1 ADMISSIBILITY: A->B (PASS), A->E (FAIL)
- G2 POLICY: B->continue (PASS), B->E/D (FAIL)
- G3 SAFETY: B->eligible (PASS), B->D/E (FAIL)
- G4 COMMIT: B->C (PASS, cross boundary), B->B/E (FAIL, never cross)

### Failure posture

- Default FAIL-CLOSED. No path to C without G4 PASS.
- Read-only flows cannot cross COMMIT_BOUNDARY.

### Evidence model

- Each transition emits: trace_id, regions, gate_id, inputs, rules+versions, authority_id, outcome, reason_code, timestamp.
- Trajectory must be reconstructible and replayable from logs.

---

## 2. Your build responsibilities

### Respect the spec first

- Always read `docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md` before proposing anything.
- That file is **normative**.

### Propose, don't execute

You MAY:
- Propose file structures (`src/`, `tests/`, `docs/` layouts)
- Sketch data structures and interfaces reflecting the geometry
- Propose NON_EXEC test cases (path tables, property lists)
- Propose diagram formats (Mermaid, PlantUML, draw.io)

You MUST NOT:
- Assume you can run code or change Git history
- Silently change invariants, regions, or gate semantics

### Files you are expected to help design

| File | Role | Status |
|------|------|--------|
| `docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md` | Canonical spec | DONE |
| `docs/LVTECH_RUNTIME_GEOMETRY_DIAGRAM_v0.1.md` | Mermaid diagram | DONE |
| `docs/LVTECH_RUNTIME_GEOMETRY_TEST_MATRIX_v0.1.md` | NON_EXEC test matrix | DONE |
| `docs/HANDOFF_PERPLEXITY.md` | This file | DONE |
| `docs/LVTECH_RUNTIME_GEOMETRY_FAQ_v0.1.md` | Optional Q&A | TODO (if requested) |

---

## 3. How to respond when asked to build

Structure your answer as:

1. **Plan section** — list tasks with file paths
2. **Per-file proposals** — path, role, content skeleton, NON_EXEC vs executable notes
3. **No-surprise rule** — if you introduce anything not in v0.1 spec:
   - Call it out explicitly
   - Propose as `v0.2 PROPOSAL`, not an edit to v0.1

---

## 4. Structural invariants (must hold in all proposals)

| # | Invariant |
|---|----------|
| 1 | No path to C without G4 PASS |
| 2 | All FAIL outcomes route to {B, D, E} |
| 3 | Enforcement rules externally versioned; runtime cannot self-modify |
| 4 | Evidence alone sufficient for replay |

---

## 5. Next bricks (future work, not yet started)

- [ ] Formal proof sketch (no path to C without G4 PASS from graph topology)
- [ ] Simulation mapping (geometry to minimal event log schema)
- [ ] Implementation planning (where each gate lives at service boundaries)
- [ ] External review (any ambiguous path? missing failure bucket?)

---

**END HANDOFF**
