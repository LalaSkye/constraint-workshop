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

Proves that MGTP `DecisionRecord` serialisation is:
- **Deterministic**: same inputs → byte-identical `canonical_bytes`
- **Stable**: same bytes → same `decision_hash` (sha256)
- **Replayable**: stored golden bytes reproduce the same hash on any run

### Input parameters

| Field | Value |
|---|---|
| `transition_id` | `txn-0001` |
| `risk_class` | `LOW` |
| `irreversible` | `false` |
| `resource_identifier` | `res://demo/alpha` |
| `trust_boundary_crossed` | `false` |
| `override_token` | `null` |
| `timestamp` | `2026-01-01T00:00:00Z` |
| `actor_id` | `demo-actor` |
| `authority_basis` | `OWNER` |
| `tenant_id` | `tenant-001` |
| `verdict` | `APPROVED` |

### canonical_bytes (base64)

```
eyJhY3Rvcl9pZCI6ImRlbW8tYWN0b3IiLCJhdXRob3JpdHlfYmFzaXMiOiJPV05FUiIsImlycmV2
ZXJzaWJsZSI6ZmFsc2UsIm92ZXJyaWRlX3Rva2VuIjpudWxsLCJyZXNvdXJjZV9pZGVudGlmaWVy
IjoicmVzOi8vZGVtby9hbHBoYSIsInJpc2tfY2xhc3MiOiJMT1ciLCJ0ZW5hbnRfaWQiOiJ0ZW5h
bnQtMDAxIiwidGltZXN0YW1wIjoiMjAyNi0wMS0wMVQwMDowMDowMFoiLCJ0cmFuc2l0aW9uX2lk
IjoidHhuLTAwMDEiLCJ0cnVzdF9ib3VuZGFyeV9jcm9zc2VkIjpmYWxzZSwidmVyZGljdCI6IkFQ
UFJPVEVEIN0=
```

### decision_hash

```
8523083fc724b22f80fb638a2518133bf03f8c3283fbe7a0f629e04da5e01200
```

### Reproduce

```bash
python examples/minimal_decision_demo.py
```

### Replay test

```bash
pytest tests/test_mgtp_replay.py -v
```

---

## Scope boundaries

`/prometheus` is an **observability-only island**. It must not be imported by any execution path, gate, or pipeline code. It observes and reports; it cannot allow, hold, deny, or silence anything.

## Licence

Apache 2.0
