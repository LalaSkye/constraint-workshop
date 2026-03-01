# Copilot Instructions — constraint-workshop

## Repo identity

This repository holds small, deterministic control primitives.
Every primitive is a single file + a test file. No frameworks. No runtime dependencies. No hidden state.

## Invariant files — DO NOT MODIFY

The following files are **frozen**. Never edit, refactor, rename, or delete them:

- `authority_gate.py`
- `stop_machine.py`
- `invariant_litmus.py`
- `commit_gate/` (entire directory)

If any suggestion would touch these paths, stop and say so instead of making the change.

## Bounded intake rule

**No implementation code may be generated until all of the following are true:**

1. A schema (data shape + field constraints) for the new primitive exists in a `.py` or `.md` file.
2. Golden tests exist that assert specific, pinned expected values (not just "it doesn't crash").
3. All golden tests are collected by `pytest` and initially fail with `NotImplementedError` or an import error — proving the tests are real and the implementation does not yet exist.

Refusing to proceed past this gate is correct behaviour, not a bug.

## Test-first order

When asked to build a new primitive, always do work in this order:

1. **Schema** — define data types, enumerations, and field constraints only. No logic.
2. **Golden tests** — write `pytest` tests that pin exact expected outputs for known inputs. Tests must fail until step 3.
3. **Implementation** — only after the user confirms the tests fail as expected.

Do not collapse these steps. Do not combine schema + implementation in one pass.

## Style rules

- Stdlib only. Do not add third-party imports unless the user explicitly approves.
- No global mutable state.
- No `random`, `uuid`, `time.time()`, `datetime.now()`, or `os.getpid()` in any primitive.
- All public functions must be pure (same input → same output, always).
- Test files are named `test_<module>.py` and live in the repo root (or `<subpackage>/tests/`).

## CI contract

CI runs `pytest -q` across Python 3.10, 3.11, 3.12.
A PR is not ready to merge until `pytest -q` passes with zero failures.

## Out of scope

Do not generate: orchestration layers, policy engines, selection logic, ML models, HTTP clients, database connections, or logging frameworks.
`/prometheus` is the observability-only sub-package (`prometheus/src/prometheus/`). It aggregates diagnostic events and reports health posture. It must not be imported by any gate, primitive, or pipeline code.
