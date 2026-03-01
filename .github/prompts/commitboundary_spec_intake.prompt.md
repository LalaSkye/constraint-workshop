# CommitBoundary Spec Intake

Use this prompt file to introduce a new primitive or spec change in a bounded, test-first way.
Run it from VS Code: **Command Palette → "Chat: Run Prompt"**, then select this file.

---

## Step 0 — Gate check

Before generating anything, confirm:

- [ ] The request does **not** touch `authority_gate.py`, `stop_machine.py`, `invariant_litmus.py`, or `commit_gate/`.

If it does, **stop here** and tell the user which protected file would be affected. Do not proceed.

---

## Step 1 — Schema only

Generate a schema file named `<primitive_name>_schema.py` containing:

- Enumerations or `TypedDict`/`NamedTuple` definitions for every data type the primitive will use.
- Field-level constraints as inline docstrings (e.g., "must be non-negative", "immutable after construction").
- A `SCHEMA_VERSION` string constant (start at `"0.1"` for new primitives; increment the minor version when updating an existing schema).
- **No logic. No methods beyond `__repr__`. No `__init__` that does computation.**

Do **not** generate an implementation file yet.

---

## Step 2 — Golden tests (fail-first)

Generate a test file named `test_<primitive_name>.py` containing:

- At least three test functions that assert **exact, pinned expected values** for known inputs.
- One test that asserts a `TypeError` or `ValueError` is raised for invalid inputs.
- One test that asserts the function/class raises `NotImplementedError` when called (proving the stub is not yet implemented).
- Import the module as if it exists: `from <primitive_name> import ...`

**All tests must fail** until the implementation exists. Confirm this by noting at the bottom of the file:

```python
# FAIL-FIRST: these tests must fail until the implementation is complete.
```

Do **not** generate an implementation file yet.

---

## Step 3 — User confirmation gate

At this point, output a summary checklist:

```
Schema file:      <primitive_name>_schema.py        ✓ generated
Golden tests:     test_<primitive_name>.py           ✓ generated (expect failures)

Next step: run `pytest test_<primitive_name>.py -v` and confirm all tests fail.
Reply "tests fail as expected" to unlock Step 4.
```

**Do not proceed to Step 4 without the user's confirmation.**

---

## Step 4 — Implementation

Only after the user confirms the tests fail:

1. Generate `<primitive_name>.py` with the minimal implementation that makes all golden tests pass.
2. Do not add features not covered by the golden tests.
3. Stdlib only — no third-party imports unless the user explicitly approved them in this session.
4. After generating, output the command to verify:

```
pytest test_<primitive_name>.py -v
```

---

## Step 5 — Final checklist

After implementation:

```
Schema:           <primitive_name>_schema.py        ✓
Golden tests:     test_<primitive_name>.py           ✓ (all passing)
Implementation:   <primitive_name>.py               ✓
CI command:       pytest -q                         (run to confirm nothing regressed)
Protected files:  authority_gate.py / stop_machine.py / invariant_litmus.py / commit_gate/   ✓ untouched
```

Do not open a PR until this checklist is complete.
