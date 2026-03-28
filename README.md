![CI](https://github.com/LalaSkye/constraint-workshop/actions/workflows/ci.yml/badge.svg)
[![CodeQL](https://github.com/LalaSkye/constraint-workshop/actions/workflows/codeql.yml/badge.svg)](https://github.com/LalaSkye/constraint-workshop/actions/workflows/codeql.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub issues](https://img.shields.io/github/issues/LalaSkye/constraint-workshop)](https://github.com/LalaSkye/constraint-workshop/issues)
[![GitHub release](https://img.shields.io/github/v/release/LalaSkye/constraint-workshop)](https://github.com/LalaSkye/constraint-workshop/releases)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)

# constraint-workshop

Three standalone, deterministic control primitives — stop machine, execution gate, invariant litmus — that compose into larger governance systems.

---

## Why This Exists

Most software control logic is implicit, buried in application code, and impossible to audit independently. These primitives make control decisions explicit, testable, and portable. Each one is a standalone brick: no frameworks, no runtime dependencies, no hidden state. Drop one in, test it in isolation, then wire it into a larger control stack. This is a primitive workbench, not a framework: no orchestration logic, no agent wrappers, no alignment policy.

---

## Architecture

```
  ┌──────────────────────────────────────────────────────────┐
  │                    constraint-workshop                    │
  │                                                          │
  │  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
  │  │  stop_machine  │  │  authority_gate  │  │  invariant_litmus    │
  │  │                │  │                  │  │                      │
  │  │ GREEN          │  │ NONE → USER      │  │ HARD_INVARIANT       │
  │  │   ↓            │  │       → OWNER    │  │ COST_CURVE           │
  │  │ AMBER          │  │       → ADMIN    │  │ EDGE                 │
  │  │   ↓ (terminal) │  │                  │  │                      │
  │  │  RED           │  │ fail-closed DENY │  │ pure phrase matching │
  │  └────────────────┘  └─────────────────┘  └──────────────────────┘
  │                                                          │
  │  ┌──────────────────────────────────────────────────┐   │
  │  │              commit_gate/ (v0.1.0)                │   │
  │  │  hash-bound commit execution gate — stdlib only   │   │
  │  └──────────────────────────────────────────────────┘   │
  │                                                          │
  │  /prometheus  — observability island (no exec imports)   │
  └──────────────────────────────────────────────────────────┘
```

---

## Primitives

### `stop_machine`

A three-state deterministic machine with fail-closed control.

| State | Meaning |
|---|---|
| `GREEN` | Normal / proceed |
| `AMBER` | Warning / caution |
| `RED` | Terminal / halt |

**Invariants:**
- RED is terminal. No advance, no reset.
- No backwards transitions (RED -> GREEN forbidden).
- Invalid transitions raise `ValueError`.
- No global state. No time logic. No optimisation.

```python
from stop_machine import State, StopMachine

m = StopMachine()      # starts GREEN
m.advance()            # -> AMBER
m.advance()            # -> RED (terminal)
m.state                # State.RED
m.advance()            # raises ValueError: RED is terminal
```

---

### `authority_gate`

An evidence-ordered access gate enforcing pre-execution admissibility. Monotonic, deterministic, pure.

| Level | Value |
|---|---|
| `NONE`  | 0 |
| `USER`  | 1 |
| `OWNER` | 2 |
| `ADMIN` | 3 |

**Invariants:**
- `required_level` is fixed at construction.
- `check()` is pure: same inputs produce same output.
- Evidence ordering is total and monotonic.
- No side effects. No logging. No state mutation.
- Fail-closed: insufficient evidence produces `DENY`.

```python
from authority_gate import Evidence, Decision, AuthorityGate

gate = AuthorityGate(Evidence.OWNER)
gate.check(Evidence.ADMIN)   # Decision.ALLOW
gate.check(Evidence.USER)    # Decision.DENY
gate.check(Evidence.NONE)    # Decision.DENY
```

---

### `invariant_litmus`

A deterministic posture classifier. Detects whether a text claim is a hard invariant (wall) or a cost curve (slope).

| Posture | Meaning |
|---|---|
| `HARD_INVARIANT` | Fundamental limit / wall |
| `COST_CURVE` | Engineering tradeoff / slope |
| `EDGE` | Ambiguous / needs clarification |

**Invariants:**
- Pure phrase matching + regex. No ML. No randomness.
- Symmetric scoring: +0.25 hard, -0.25 cost, +0.15 quantification.
- Negation handling: 2-word window.
- No external dependencies beyond `re`.

```python
from invariant_litmus import classify, Posture

r = classify("Shannon limit provides an upper bound")
r.posture   # Posture.HARD_INVARIANT
r.score     # 0.5
r.signals   # [("hard", "shannon limit"), ("hard", "upper bound")]

r2 = classify("latency can be reduced by adding cache")
r2.posture  # Posture.COST_CURVE
```

---

## Commit Gate Engine (v0.1.0)

Deterministic, hash-bound commit execution gate — stdlib-only, no network, no new governance primitives. Enforces the commit boundary: no execution without explicit, evidence-backed authority.

- **Location:** [`/commit_gate/`](commit_gate/)
- **Proves:** determinism (byte-identical output across runs) + drift-fail (reachability expansion without contract revision is rejected)
- **Release:** [`commit_gate-v0.1.0`](https://github.com/LalaSkye/constraint-workshop/releases/tag/commit_gate-v0.1.0)
- **CI:** [`commit_gate_ci.yml`](https://github.com/LalaSkye/constraint-workshop/actions/workflows/commit_gate_ci.yml) — Python 3.10 / 3.11 / 3.12 matrix

---

## Run Tests

```bash
git clone https://github.com/LalaSkye/constraint-workshop.git
cd constraint-workshop
pip install pytest
pytest test_stop_machine.py test_authority_gate.py test_invariant_litmus.py -v
```

Expected output (all passing):

```
test_stop_machine.py::test_initial_state PASSED
test_stop_machine.py::test_advance_to_amber PASSED
test_stop_machine.py::test_advance_to_red PASSED
test_stop_machine.py::test_red_is_terminal PASSED
test_authority_gate.py::test_allow_admin PASSED
test_authority_gate.py::test_deny_user PASSED
test_invariant_litmus.py::test_hard_invariant_signal PASSED
...
```

---

## Scope Boundaries

`/prometheus` is an **observability-only island**. It must not be imported by any execution path, gate, or pipeline code. It observes and reports; it cannot allow, hold, deny, or silence anything.

---

## LV/Tech Runtime Governance Geometry

This repo uses a spec-first workflow for runtime governance. The canonical runtime governance geometry is defined in:

- [`docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md`](docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md) — Canonical spec
- [`docs/LVTECH_RUNTIME_GEOMETRY_DIAGRAM_v0.1.md`](docs/LVTECH_RUNTIME_GEOMETRY_DIAGRAM_v0.1.md) — Mermaid diagram
- [`docs/LVTECH_RUNTIME_GEOMETRY_TEST_MATRIX_v0.1.md`](docs/LVTECH_RUNTIME_GEOMETRY_TEST_MATRIX_v0.1.md) — NON_EXEC test matrix

It describes state-space regions (A–E), deterministic gates (G1–G4), a one-way commit boundary, fail-closed control posture, and evidence and audit requirements.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Code of conduct in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Engineering status in [ENGINEERING_STATUS.yaml](ENGINEERING_STATUS.yaml).

---

## Part of the Execution Boundary Series

| Repo | Layer | What It Does |
|---|---|---|
| [interpretation-boundary-lab](https://github.com/LalaSkye/interpretation-boundary-lab) | Upstream boundary | 10-rule admissibility gate for interpretations |
| [dual-boundary-admissibility-lab](https://github.com/LalaSkye/dual-boundary-admissibility-lab) | Full corridor | Dual-boundary model with pressure monitoring and C-sector rotation |
| [execution-boundary-lab](https://github.com/LalaSkye/execution-boundary-lab) | Execution boundary | Demonstrates cascading failures without upstream governance |
| [stop-machine](https://github.com/LalaSkye/stop-machine) | Control primitive | Deterministic three-state stop controller |
| [constraint-workshop](https://github.com/LalaSkye/constraint-workshop) | Control primitives | Execution gate, invariant litmus, stop machine |
| [csgr-lab](https://github.com/LalaSkye/csgr-lab) | Measurement | Contracted stability and drift measurement |
| [invariant-lock](https://github.com/LalaSkye/invariant-lock) | Drift prevention | Refuse execution unless version increments |
| [policy-lint](https://github.com/LalaSkye/policy-lint) | Policy validation | Deterministic linter for governance statements |
| [deterministic-lexicon](https://github.com/LalaSkye/deterministic-lexicon) | Vocabulary | Fixed terms, exact matches, no inference |

---

## Work With Me

Need governance tooling for your AI systems? I consult on runtime constraint design, AI governance architecture, and EU AI Act compliance.

→ **ricky.mcjones@gmail.com**
→ [LinkedIn](https://linkedin.com/in/ricky-jones-1b745474)
→ [GitHub Sponsors](https://github.com/sponsors/LalaSkye)

---

## License

Apache 2.0. See `LICENSE`.

---

## Authorship & Rights

All architecture, methods, and system designs in this repository are the original work of **Ricky Dean Jones** unless otherwise stated.
No rights to use, reproduce, or implement are granted without explicit permission beyond the terms of the repository licence.

**Author:** Ricky Dean Jones
**Repository owner:** [LalaSkye](https://github.com/LalaSkye)
**Status:** Active research / architecture work
**Part of:** [Execution Boundary Series](https://github.com/LalaSkye) — TrinityOS / AlvianTech

---

This repository demonstrates deterministic control using standard engineering techniques. No proprietary frameworks or external implementations are used.

