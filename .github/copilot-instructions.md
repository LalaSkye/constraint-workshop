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

## Pull request checklist

Before opening a PR, verify:
1. All new primitives have a matching `test_<module>.py`.
2. `pytest` passes with zero failures.
3. No new runtime dependencies introduced.
4. README updated if the public interface changed.
5. If a new `CommitRequest` field is added, update `canonicalise.py` and regenerate baselines.
