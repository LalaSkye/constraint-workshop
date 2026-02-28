![CI](https://github.com/LalaSkye/constraint-workshop/actions/workflows/ci.yml/badge.svg)

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

## Deterministic Decision Artefact Demo

Proves: same inputs → same bytes → same hash → replay works.

### Input parameters

| Field | Value |
|-------|-------|
| `actor_id` | `demo-actor` |
| `action_class` | `FILE` |
| `context.description` | `minimal demo commit` |
| `authority_scope.project` | `demo-project` |
| `invariant_hash` | `0000…0000` (64 zeros) |
| Ruleset | allowlist: `demo-actor / FILE / demo-project` |

### Output artefact

```
verdict        : ALLOW
decision_hash  : fab8740c920489154038063620e1453460e1ea1549d0cb1f0cb2dca0ce860360
canonical_bytes (base64, first 64 chars):
eyJhcnRlZmFjdF92ZXJzaW9uIjoiMC4xIiwiZGVjaXNpb25faGFzaCI6ImZhYj…
```

Full base64 stored in [`tests/fixtures/golden_canonical_bytes.b64`](tests/fixtures/golden_canonical_bytes.b64).

### Reproduce

```bash
python examples/minimal_decision_demo.py
```

### Replay test

```bash
pytest tests/test_replay_decision.py -v
```

---

## Scope boundaries

`/prometheus` is an **observability-only island**. It must not be imported by any execution path, gate, or pipeline code. It observes and reports; it cannot allow, hold, deny, or silence anything.

## Licence

Apache 2.0
