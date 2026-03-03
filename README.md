![CI](https://github.com/LalaSkye/constraint-workshop/actions/workflows/ci.yml/badge.svg)
[![CodeQL](https://github.com/LalaSkye/constraint-workshop/actions/workflows/codeql.yml/badge.svg)](https://github.com/LalaSkye/constraint-workshop/actions/workflows/codeql.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub issues](https://img.shields.io/github/issues/LalaSkye/constraint-workshop)](https://github.com/LalaSkye/constraint-workshop/issues)
[![GitHub release](https://img.shields.io/github/v/release/LalaSkye/constraint-workshop)](https://github.com/LalaSkye/constraint-workshop/releases)

# constraint-workshop

Small, deterministic control primitives for software systems. Testable, auditable bricks.

## Why this exists

Most software control logic is implicit, buried in application code, and impossible to audit independently. These primitives make control decisions explicit, testable, and portable. Each one is a standalone brick: no frameworks, no runtime dependencies, no hidden state. If your system needs a verifiable stop condition, a gated authority check, or a deterministic posture classifier, you can drop one in and test it in isolation.

## Primitives

### `stop_machine`

A three-state deterministic machine.

| State | Meaning |
|-------|---------------------|
| GREEN | Normal / proceed |
| AMBER | Warning / caution |
| RED | Terminal / halt |

**Invariants:**
  - RED is terminal. No advance, no reset.
  - No skipping backwards (RED -> GREEN forbidden).
  - Invalid transitions raise `ValueError`.
  - No global state. No time logic. No optimisation.

**Interface:**
  ```python
  from stop_machine import State, StopMachine

  m = StopMachine()      # starts GREEN
  m.advance()            # -> AMBER
  m.advance()            # -> RED (terminal)
  m.state                # State.RED
  ```

---

### `authority_gate`

An evidence-ordered access gate. Monotonic, deterministic, pure.

| Level | Value |
|-------|-------|
| NONE  | 0     |
| USER  | 1     |
| OWNER | 2     |
| ADMIN | 3     |

**Invariants:**
  - required_level is fixed at construction.
  - check() is pure: same inputs produce same output.
  - Evidence ordering is total and monotonic.
  - No side effects. No logging. No state mutation.

**Interface:**
  ```python
  from authority_gate import Evidence, Decision, AuthorityGate

  gate = AuthorityGate(Evidence.OWNER)
  gate.check(Evidence.ADMIN)   # Decision.ALLOW
  gate.check(Evidence.USER)    # Decision.DENY
  ```

---

### `invariant_litmus`

A deterministic posture classifier. Detects whether a text claim is a hard invariant (wall) or a cost curve (slope).

| Posture | Meaning |
|---------|-------------------------------|
| HARD_INVARIANT | Fundamental limit / wall |
| COST_CURVE | Engineering tradeoff / slope |
| EDGE | Ambiguous / needs clarification |

**Invariants:**
  - Pure phrase matching + regex. No ML. No randomness.
  - Symmetric scoring: +0.25 hard, -0.25 cost, +0.15 quantification.
  - Negation handling: 2-word window.
  - No external dependencies beyond `re`.

**Interface:**
  ```python
  from invariant_litmus import classify, Posture

  r = classify("Shannon limit provides an upper bound")
  r.posture   # Posture.HARD_INVARIANT
  r.score     # 0.5
  r.signals   # [("hard", "shannon limit"), ("hard", "upper bound")]
  ```

## Run Tests

```bash
pip install pytest
pytest test_stop_machine.py test_authority_gate.py test_invariant_litmus.py -v
```


## Commit Gate Engine (v0.1.0)

Deterministic, hash-bound commit authority gate — stdlib-only, no network, no new governance primitives.

- **Location:** [`/commit_gate/`](commit_gate/)
- **Proves:** determinism (byte-identical output across runs) + drift-fail (reachability expansion without contract revision is rejected)
- **Release:** [`commit_gate-v0.1.0`](https://github.com/LalaSkye/constraint-workshop/releases/tag/commit_gate-v0.1.0)
- **CI:** [`commit_gate_ci.yml`](https://github.com/LalaSkye/constraint-workshop/actions/workflows/commit_gate_ci.yml) (Python 3.10/3.11/3.12 matrix)
- **Proof:** Determinism + drift-fail validated across Python 3.10/3.11/3.12.

## Scope boundaries

`/prometheus` is an **observability-only island**. It must not be imported by any execution path, gate, or pipeline code. It observes and reports; it cannot allow, hold, deny, or silence anything.

## Licence

Apache 2.0


## LV/Tech Runtime Governance Geometry

This repo uses a **spec-first** workflow for runtime governance.

The canonical runtime governance geometry is defined in:

- [`docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md`](docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md) — Canonical spec
- [`docs/LVTECH_RUNTIME_GEOMETRY_DIAGRAM_v0.1.md`](docs/LVTECH_RUNTIME_GEOMETRY_DIAGRAM_v0.1.md) — Mermaid diagram
- [`docs/LVTECH_RUNTIME_GEOMETRY_TEST_MATRIX_v0.1.md`](docs/LVTECH_RUNTIME_GEOMETRY_TEST_MATRIX_v0.1.md) — NON_EXEC test matrix
- [`docs/HANDOFF_PERPLEXITY.md`](docs/HANDOFF_PERPLEXITY.md) — AI assistant builder instructions

It describes:

- State-space regions (A–E)
- Deterministic gates (G1–G4)
- A one-way commit boundary
- Fail-closed failure posture
- Evidence and audit requirements

### How to work with AI assistants

When you use Perplexity or another assistant on this repo:

1. Point it at the geometry spec.
2. Ask it to **propose** docs, diagrams, and NON_EXEC test matrices first.
3. Only after HUMAN review, ask for executable code that **implements** the geometry without changing its invariants.

See [`docs/HANDOFF_PERPLEXITY.md`](docs/HANDOFF_PERPLEXITY.md) for full builder instructions.
