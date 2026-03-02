# decision_space_ledger

Deterministic inspection utility for versioned decision-space snapshots.

**Inspection only.**  This primitive does not modify any enforcement, gating, authority, or runtime logic.  It reads snapshots, validates them, canonicalises them, hashes them, and produces structured diffs.

---

## Schema — `decision_space_snapshot_v1`

| Field | Type | Constraints |
|-------|------|-------------|
| `version` | string | Must be exactly `"v1"` |
| `variables` | array of strings | Unique items |
| `allowed_transitions` | array of `{from, to}` objects | Each item has exactly `from` (string) and `to` (string) |
| `exclusions` | array of strings | Unique items |
| `reason_code_families` | object → array of strings | Each value array has unique items |

The canonical JSON Schema (draft-07) is in `src/decision_space_ledger/decision_space_snapshot_v1.schema.json`.

---

## Invariants

| # | Invariant |
|---|-----------|
| 1 | `validate()` raises `ValueError` for any schema violation — no silent pass-through |
| 2 | `canonicalise()` is order-independent: logically equivalent snapshots produce byte-identical output |
| 3 | `canonical_hash()` is exactly 64 lowercase hex characters (SHA-256) |
| 4 | Same inputs always produce the same outputs (deterministic, no randomness, no global state) |
| 5 | `diff()` output lists are always sorted (deterministic across runs) |
| 6 | No side effects — no I/O, no logging, no state mutation |

---

## Interface

```python
from decision_space_ledger import validate, canonicalise, canonical_hash, diff

snapshot = {
    "version": "v1",
    "variables": ["APPROVE", "DENY", "HOLD"],
    "allowed_transitions": [
        {"from": "HOLD", "to": "APPROVE"},
        {"from": "HOLD", "to": "DENY"},
    ],
    "exclusions": [],
    "reason_code_families": {
        "approval": ["MANUAL", "AUTO"],
    },
}

validate(snapshot)             # raises ValueError on any violation
h = canonical_hash(snapshot)   # 64-char lowercase hex SHA-256
delta = diff(snapshot, other)  # structured diff dict
```

---

## CLI

Compare two snapshot files:

```bash
python -m decision_space_ledger snapshot_a.json snapshot_b.json
```

Output (JSON to stdout):

```json
{
  "snapshot_a": {"path": "snapshot_a.json", "hash": "<sha256>"},
  "snapshot_b": {"path": "snapshot_b.json", "hash": "<sha256>"},
  "diff": {
    "is_identical": false,
    "variables_added": ["NEW_STATE"],
    "variables_removed": [],
    "transitions_added": [{"from": "HOLD", "to": "NEW_STATE"}],
    "transitions_removed": [],
    "exclusions_added": [],
    "exclusions_removed": [],
    "reason_code_families_added": [],
    "reason_code_families_removed": [],
    "reason_code_families_changed": {}
  }
}
```

Exit codes: `0` success, `1` I/O or validation error, `2` incorrect usage.

---

## Run Tests

```bash
pytest decision_space_ledger/tests/ -v
```

Or from the repository root (tests are discovered automatically):

```bash
pytest -q
```

---

## Module layout

```
decision_space_ledger/
  src/decision_space_ledger/
    __init__.py                          # public exports
    schema.py                            # SCHEMA constant + validate()
    decision_space_snapshot_v1.schema.json  # JSON Schema draft-07 reference
    canonicalise.py                      # canonicalise() + canonical_hash()
    diff.py                              # diff()
    cli.py                               # CLI main()
    __main__.py                          # python -m entry point
  tests/
    test_ledger.py                       # full unit tests (62 tests)
  README.md
```
