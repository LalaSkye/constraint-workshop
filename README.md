# constraint-workshop

Small, deterministic control primitives for software systems. Testable, auditable bricks.

## Primitives

### `stop_machine`

A three-state deterministic machine.

| State | Meaning |
|-------|-------------------|
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

## Run Tests

```bash
pip install pytest
pytest test_stop_machine.py -v
```

## Licence

Apache 2.0
