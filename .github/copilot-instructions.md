# Copilot Instructions for constraint-workshop

## Repository purpose

This repository contains small, deterministic control primitives for software systems.
Each primitive is a standalone, testable, auditable brick with no framework dependencies,
no runtime state, and no hidden behavior.

## Coding standards

- **stdlib only** — no third-party runtime dependencies unless explicitly approved.
- **Deterministic** — same inputs must always produce the same outputs; no randomness, no time-dependent logic, no global state.
- **No side effects** — primitives must not log, mutate shared state, or perform I/O.
- **Pure Python** — target Python 3.10–3.12. Avoid walrus operators or syntax unavailable on 3.10.
- **Tests mandatory** — every primitive ships with a `pytest` test file. Tests must cover all invariants stated in the module docstring.
- **No ML / no network** — classifiers use phrase matching and regex only.

## Module layout conventions

```
<module>/
  src/<module>/   # source package (importable)
  tests/          # pytest tests
  rules/          # declarative JSON rule files (where applicable)
  baselines/      # hash-bound baseline artefacts (where applicable)
  README.md       # contract + usage
```

## Commit Gate specifics

- Verdicts are exactly: `ALLOW`, `REFUSE`, `ESCALATE` — no new verdict values.
- Scope matching is **exact string match only** — no glob, no regex, no prefix.
- `invariant_hash` is SHA-256 of the declared contract text (hex, lowercase, 64 chars).
- `decision_hash` is SHA-256 of `canonical_request + verdict + sorted(reasons)`.
- Authority drift detection: new allowlist edges with an unchanged `invariant_hash` must **FAIL**.
- The `/prometheus/` directory is observability-only and must never be imported by gate/engine code.

## Invariant litmus specifics

- Scoring: `+0.25` hard-invariant signal, `-0.25` cost-curve signal, `+0.15` quantification signal.
- Negation window: 2 words.
- No external dependencies beyond `re`.

## Hard decision invariants (enforced by all gate primitives)

These rules are non-negotiable and must be encoded in every gate, engine, and policy primitive:

1. **Fail-closed defaults** — if policy, identity, or logging is missing, the decision is `DENY`.
2. **No silent success** — every decision must produce a Receipt; if a Receipt cannot be created, the decision is `DENY`.
3. **No self-approval** — `actor_id` cannot appear as an approver for the same request; if it does, the decision is `DENY`.
4. **Approval required but absent** — if approval is required and no valid approval is present, the decision is `HOLD` (never `ALLOW`).
5. **Tamper-evident log** — Receipts carry `{seq, prev_hash, this_hash}`; any out-of-order sequence or invalid hash linkage must be rejected.

## Process rules

- **Prefer schemas + conformance tests before implementation.** Define the JSON schema and golden test vectors first; open a separate PR for the implementation.
- **PRs must be small and reviewable.** One primitive or one contract change per PR.
- **No scope expansion.** A PR that adds new verdicts, new primitives, or new cross-module imports without a preceding schema PR must be rejected.

## Pull request checklist

Before opening a PR, verify:
1. All new primitives have a matching `test_<module>.py`.
2. `pytest` passes with zero failures.
3. No new runtime dependencies introduced.
4. README updated if the public interface changed.
5. If a new `CommitRequest` field is added, update `canonicalise.py` and regenerate baselines.
