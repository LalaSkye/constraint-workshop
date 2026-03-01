# Evidence Map

Generated from repo truth. No architecture proposed — only pointing to what exists.

## Key file paths

| Artefact | Path |
|---|---|
| Gate primitive (engine) | `commit_gate/src/commit_gate/engine.py` |
| Canonicalisation | `commit_gate/src/commit_gate/canonicalise.py` |
| Drift detector | `commit_gate/src/commit_gate/drift.py` |
| CLI (verifier entry point) | `commit_gate/src/commit_gate/cli.py` |
| Ruleset (decision schema) | `commit_gate/rules/ruleset.json` |
| Authority graph baseline | `commit_gate/baselines/authority_graph.json` |
| Determinism tests | `commit_gate/tests/test_determinism.py` |
| Drift tests | `commit_gate/tests/test_drift.py` |
| CI workflow — general | `.github/workflows/ci.yml` |
| CI workflow — commit gate | `.github/workflows/commit_gate_ci.yml` |
| Prometheus observability | `prometheus/src/prometheus/` |
| Prometheus tests | `prometheus/tests/` |
| Stop-machine primitive | `stop_machine.py` |
| Authority-gate primitive | `authority_gate.py` |
| Invariant litmus primitive | `invariant_litmus.py` |

## Determinism test coverage

The following tests exist in `commit_gate/tests/test_determinism.py`:

| Test | What it proves |
|---|---|
| `test_t1_determinism` | Same input → byte-identical output artefact (two calls) |
| `test_t2_hash_stability` | `request_hash` is stable across calls; length and case validated |
| `test_t3_ordering` | Key ordering and `reasons` list are stable regardless of insertion order |
| `test_verdict_allow` | Allowlist match → `ALLOW` verdict |
| `test_verdict_refuse_denylist` | Denylist match → `REFUSE` verdict |
| `test_verdict_escalate` | Escalation match → `ESCALATE` verdict |
| `test_verdict_default_refuse` | No match → default `REFUSE` |
| `test_scope_superset_allowed` | Superset scope keys still match rule |
| `test_artefact_version` | Artefact version is `0.1` |

**Golden-hash pinned constants** (fixed SHA-256 → fixed output) are not currently in the test suite.
They were proposed but require explicit authority to add (see `OUTSTANDING_WORK_RISK_REPORT.md`).

## Commands to run tests locally

```bash
# All tests (commit_gate + prometheus + top-level primitives)
pip install pytest
pytest -q

# commit_gate only
cd commit_gate
python -m pytest tests/ -v

# prometheus only
bash scripts/test_prometheus.sh
# or directly:
python -m pytest prometheus/tests/ -v

# Top-level primitives only
pytest test_stop_machine.py test_authority_gate.py test_invariant_litmus.py -v
```

## GitHub Actions workflow names

| Workflow file | Workflow name | Trigger |
|---|---|---|
| `.github/workflows/ci.yml` | `ci` | push / pull_request (all paths) |
| `.github/workflows/commit_gate_ci.yml` | `Commit Gate CI` | push / pull_request on `commit_gate/**` |

## Post-ready proof links

| Label | URL |
|---|---|
| Main repo | https://github.com/LalaSkye/constraint-workshop |
| Gate primitive directory | https://github.com/LalaSkye/constraint-workshop/tree/main/commit_gate/src/commit_gate |
| Determinism test file | https://github.com/LalaSkye/constraint-workshop/blob/main/commit_gate/tests/test_determinism.py |
| CLI / verifier script | https://github.com/LalaSkye/constraint-workshop/blob/main/commit_gate/src/commit_gate/cli.py |
| Actions runs (Commit Gate CI) | https://github.com/LalaSkye/constraint-workshop/actions/workflows/commit_gate_ci.yml |
| Latest release / tag | https://github.com/LalaSkye/constraint-workshop/releases/tag/commit_gate-v0.1.0 |
