# Contributing to constraint-workshop

Thanks for considering a contribution.

## Ground Rules
1. **Read the geometry spec first** (`docs/LVTECH_RUNTIME_GEOMETRY_v0.1.md`).
2. **No scope drift** — every change must trace back to an existing spec or open issue.
3. **Fail-closed by default** — if in doubt, reject. Never silently pass.
4. **NON_EXEC artefacts first** — propose docs, diagrams, or test matrices before writing executable code.

## Workflow
1. Fork the repo.
2. Create a feature branch from `main`.
3. Write your change with tests (see `docs/LVTECH_RUNTIME_GEOMETRY_TEST_MATRIX_v0.1.md`).
4. Run `ruff check .` and `pytest -q` locally.
5. Open a PR against `main` with a clear description linking the relevant issue.

## Code Style
- Python: follow `ruff` defaults.
- Markdown: one sentence per line where possible.
- YAML: 2-space indent, quoted strings.

## Reviews
- All PRs require at least one approving review.
- Gate-review labelled issues require explicit human sign-off before implementation.

## Reporting Issues
See [SECURITY.md](SECURITY.md) for vulnerability reports.
For everything else, open a GitHub issue with a clear title and repro steps.
