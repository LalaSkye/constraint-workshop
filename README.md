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

## Licence

Apache 2.0
