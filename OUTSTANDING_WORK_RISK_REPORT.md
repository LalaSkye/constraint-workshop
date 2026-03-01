# OUTSTANDING WORK & RISK REPORT

**Repository:** LalaSkye/constraint-workshop  
**Branch audited:** feat/mgtp-scaffold-v0.1 (current HEAD: `078c479`, basis for all open PRs)  
**Report date:** 2026-03-01  
**Scope:** Read-only inspection. No code changes made.

---

## 1. Open Pull Requests

### PR #14 — [WIP] Produce outstanding work audit report for governance

| Field | Value |
|---|---|
| Title | [WIP] Produce outstanding work audit report for governance |
| State | Open — Draft |
| Base branch | `main` |
| Head branch | `copilot/outstanding-work-audit-report` |
| Lines changed | 0 (no files modified in the single commit `cfa0579 "Initial plan"`) |
| ci.yml status | `action_required` — workflow queued but not executed; requires repository owner approval before GitHub Actions will run jobs (run ID 22540458847, 0 jobs started) |
| Commit Gate CI status | Not triggered — no `commit_gate/**` paths touched |
| Merge conflicts | No (`mergeable_state: blocked` — blocked by draft status and pending CI, not by conflict) |
| Overlap with merged PRs | None — no files changed |
| Risk level | LOW — zero code change; deliverable (this report) not yet committed |
| Recommendation | **HOLD** — merge only after report file is committed and CI passes |

**Merged PRs (reference)**

| PR | Title | Merged | Commit |
|---|---|---|---|
| #12 | chore: add .gitignore, remove binary artefact risk, add CI guardrails | 2026-02-28 | `078c479` |

PR #12 introduced: `.gitignore`, `.github/workflows/ci.yml` (with binary-artefact and protected-file guards), `.github/workflows/commit_gate_ci.yml`, and all source files (`authority_gate.py`, `stop_machine.py`, `invariant_litmus.py`, `commit_gate/`, `prometheus/`, `docs/`, test files). This is the sole prior merge; the entire codebase landed in one commit.

---

## 2. Branch Surface Integrity

### Forbidden paths

| Path | Modified on this branch vs `main`? | Evidence |
|---|---|---|
| `authority_gate.py` | No | `git show cfa0579 --stat` shows 0 files changed |
| `stop_machine.py` | No | Same |
| `commit_gate/**` | No | Same |

All three forbidden paths are untouched on branch `copilot/outstanding-work-audit-report`.

### Binary artefacts

`git ls-files` on the working tree returns no entries matching `__pycache__/` or `*.py[cod]`. No binary artefacts are tracked.

### `.gitignore` enforcement

File present at `.gitignore`. Covers: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `.env`, `.venv`, `dist/`, `build/`.

### CI guards

Both guards are defined in `.github/workflows/ci.yml`:

1. **Binary artefact check** — `git ls-files | grep -qE '(__pycache__|\.py[cod]$)'` → exits 1 on match.
2. **Protected file check** — `git fetch origin main --depth=1 && git diff --name-only origin/main...HEAD | grep -qE '^(authority_gate\.py|stop_machine\.py|commit_gate/)'` → exits 1 on match.

Guards are present. For PR #14 they have not executed (CI is in `action_required` state pending owner approval of the bot workflow).

---

## 3. Determinism Guarantees

### `canonical_bytes` / `canonicalise` implementation

| Item | Location |
|---|---|
| Function | `commit_gate/src/commit_gate/canonicalise.py` — `canonicalise(obj)` |
| Method | `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")` |
| Hash function | `canonical_hash(obj)` — `hashlib.sha256(canonicalise(obj)).hexdigest()` (lowercase hex, 64 chars) |

Rules enforced: UTF-8 encoding, recursively sorted keys, no whitespace, list order preserved (caller responsibility).

### Golden fixture tests

`commit_gate/tests/test_determinism.py::test_t2_hash_stability` verifies that `canonical_hash` returns a stable 64-character lowercase hex string across two calls. It does **not** assert a pinned known hash value. No test in the repository pins a concrete SHA-256 hex string as an expected golden value.

`prometheus/tests/test_input_hashing.py::test_sha256_stable_across_runs` verifies format (64 chars) and cross-call stability. Again, no pinned value.

**Gap:** No test asserts a specific expected hash for a known input. Golden regression tests (pinning a known digest) are absent.

### Multi-iteration stability tests

| Test | Iterations | Location |
|---|---|---|
| `test_deterministic_across_calls` (authority_gate) | 100 | `test_authority_gate.py` |
| `test_deterministic_across_runs` (stop_machine) | 100 | `test_stop_machine.py` |
| `test_deterministic_across_calls` (invariant_litmus) | 100 | `test_invariant_litmus.py` |
| `test_t1_determinism` (commit_gate evaluate) | 2 | `commit_gate/tests/test_determinism.py` |
| `test_summarise_identical_for_identical_inputs` (prometheus) | 2 | `prometheus/tests/test_aggregation_determinism.py` |

### CI matrix cross-version

Both `ci.yml` and `commit_gate_ci.yml` run against Python 3.10, 3.11, 3.12 on `ubuntu-latest`. Cross-version execution is defined but has not run for PR #14 (action_required state).

### Remaining entropy sources

No use of `random`, `uuid`, `time.time()`, `datetime.now()`, `os.getpid()`, or `threading` found in any core module (`authority_gate.py`, `stop_machine.py`, `invariant_litmus.py`, `commit_gate/src/`, `prometheus/src/`).

Residual risk: `os.walk` in `prometheus/src/prometheus/redlines.py::scan_text_files` returns directory entries in filesystem order. The function applies `sorted()` before returning. Explicit sort is present; no residual directory-traversal entropy.

---

## 4. Evaluation Entry Points

### Public functions

| Function | Module | Signature |
|---|---|---|
| `evaluate` | `commit_gate/src/commit_gate/engine.py` | `evaluate(commit_request: dict, ruleset: dict) -> dict` |
| `build_request_obj` | `commit_gate/src/commit_gate/engine.py` | `build_request_obj(actor_id, action_class, context, authority_scope, invariant_hash) -> dict` |
| `load_ruleset` | `commit_gate/src/commit_gate/engine.py` | `load_ruleset(path) -> dict` |
| `write_decision_report` | `commit_gate/src/commit_gate/engine.py` | `write_decision_report(verdict_dict, request_hash, output_dir) -> Path` |
| `detect_drift` | `commit_gate/src/commit_gate/drift.py` | `detect_drift(baseline_graph, current_graph, baseline_invariant_hash, current_invariant_hash, acknowledge_expansion) -> dict` |
| `build_authority_graph` | `commit_gate/src/commit_gate/drift.py` | `build_authority_graph(ruleset) -> dict` |
| `AuthorityGate.check` | `authority_gate.py` | `check(provided: Evidence) -> Decision` |
| `classify` | `invariant_litmus.py` | `classify(text: str) -> LitmusResult` |
| `summarise` | `prometheus/src/prometheus/aggregate.py` | `summarise(events, window_start, window_end, input_hash) -> dict` |
| `run_from_fixture_set` | `prometheus/src/prometheus/render.py` | `run_from_fixture_set(prometheus_dir, rules) -> tuple` |

### Canonical entrypoint

`evaluate()` in `commit_gate/src/commit_gate/engine.py` is the canonical commit-gate resolution function. It is also exposed via CLI: `python -m commit_gate evaluate --request REQUEST.json --ruleset RULESET.json`.

### Duplication / ambiguity

No duplication of the `evaluate` function is present. `build_request_obj` is a helper exposed publicly but only used internally and in tests; it is not a second evaluation entrypoint.

`classify` exists in two unrelated modules: `invariant_litmus.py` (posture classification) and `prometheus/src/prometheus/fit_report.py` (health verdict classification). These are distinct functions in separate namespaces with different signatures and return types. No ambiguity in imports as long as callers use fully-qualified module paths.

### Consolidation recommendation

No consolidation required for existing functions. If `prometheus/fit_report.classify` is exported as part of a public API in the future, renaming it (e.g., `classify_fit`) would prevent collision with `invariant_litmus.classify`.

---

## 5. DecisionRecord Artefact Status

### Fields present in verdict dict

`commit_gate/src/commit_gate/engine.py::evaluate()` returns:

| Field | Present | Notes |
|---|---|---|
| `verdict` | Yes | ALLOW, REFUSE, or ESCALATE |
| `reasons` | Yes | Sorted list of reason strings |
| `decision_hash` | Yes | SHA-256 of `{request_obj, verdict, reasons}` |
| `request_hash` | Yes | SHA-256 of request object (timestamp excluded) |
| `artefact_version` | Yes | Hardcoded `"0.1"` |

### Time-bound enforcement logic

`timestamp_utc` is described in the docstring of `evaluate()` as "optional" in the commit request. It is **not included** in `request_obj` (the hashable object) and is **not validated** or enforced anywhere in `engine.py`. No expiry window, no staleness check, no time-bound rejection path exists.

**Gap:** Time-bound enforcement is absent.

### Evidence enforcement logic

`invariant_hash` is accepted as a field of `commit_request` and is included in `request_obj` for hashing purposes. It is **not validated** against any canonical or expected hash value inside `evaluate()`. No enforcement logic checks that `invariant_hash` matches a known contract value.

**Gap:** `invariant_hash` is recorded but not enforced.

### Replay demonstration

No replay demonstration script, notebook, or test exists. The CLI (`python -m commit_gate evaluate`) can replay a request given a fixed JSON file, but no fixture or test demonstrates deterministic replay producing an identical `decision_hash`.

**Gap:** Replay demonstration absent.

### Verdict path coverage

| Path | Verdict | Test |
|---|---|---|
| Allowlist match | ALLOW | `commit_gate/tests/test_determinism.py::test_verdict_allow` |
| Denylist match | REFUSE | `commit_gate/tests/test_determinism.py::test_verdict_refuse_denylist` |
| Default (no match) | REFUSE | `commit_gate/tests/test_determinism.py::test_verdict_default_refuse` |
| Escalation match | ESCALATE | `commit_gate/tests/test_determinism.py::test_verdict_escalate` |
| SUPERVISED | — | **Not defined.** No `SUPERVISED` verdict exists in `engine.py`. Closest equivalent is `ESCALATE`. |

---

## 6. CI & Workflow Integrity

### Workflows

| File | Trigger | Matrix | Purpose |
|---|---|---|---|
| `.github/workflows/ci.yml` | push, pull_request (all paths) | Python 3.10, 3.11, 3.12 | Root tests + binary-artefact + protected-file guards |
| `.github/workflows/commit_gate_ci.yml` | push/PR on `commit_gate/**` | Python 3.10, 3.11, 3.12 | `commit_gate/tests/` only |

### Required status checks on `main`

Branch protection rules cannot be read via the tools available for this report. Required status checks are not confirmed from inspection alone.

### Historical CI state

The most recent workflow run (run ID 22540458847, PR #14) completed with conclusion `action_required`. This is a GitHub Actions first-time-contributor approval gate, not a test failure. Zero jobs were executed.

The prior merged state (commit `078c479`, PR #12) passed CI before merge — this is inferred from the merge having been accepted by the repository owner.

### Missing dependency installs

`ci.yml` installs only `pip install pytest`. Sub-packages (`commit_gate`, `prometheus`) are **not installed** as packages. Tests work because:
- `commit_gate/tests/test_determinism.py` and `test_drift.py` prepend `../src` to `sys.path` manually.
- `prometheus/tests/conftest.py` prepends `../src` to `sys.path` via a shared fixture.

This is functional but fragile. If test discovery changes or tests are run from a different working directory, the path hacks may break. No `pyproject.toml`, `setup.py`, or `setup.cfg` was found in `commit_gate/` or `prometheus/`.

**Gap:** Sub-packages not installed as editable packages; path manipulation is manual and per-file.

---

## 7. Architecture Drift Scan

### Scope as stated

The stated scope is: Determinism hardening, Artefact enforcement, Test strengthening.

### Findings

| Module | Files | Classification |
|---|---|---|
| `authority_gate.py` | 1 | In scope — artefact primitive |
| `stop_machine.py` | 1 | In scope — artefact primitive |
| `invariant_litmus.py` | 1 | In scope — artefact primitive |
| `commit_gate/src/commit_gate/` | 6 | In scope — determinism + artefact enforcement |
| `commit_gate/tests/` | 2 | In scope — test strengthening |
| `prometheus/src/prometheus/` | 8 | **Expansion** — see below |
| `prometheus/tests/` | 6 | Partially in scope (test strengthening for prometheus) |
| `scripts/test_prometheus.sh` | 1 | In scope — test runner |

### `prometheus/` expansion

`prometheus/src/prometheus/` introduces:

| Module | Function |
|---|---|
| `aggregate.py` | Event aggregation (`Counter`-based) |
| `fit_report.py` | FIT_CLEAN / FIT_WITH_WARNINGS / DRIFT_RISK classification |
| `hashing.py` | File set hashing (SHA-256 over ordered JSONL files) |
| `io_jsonl.py` | JSONL read/write |
| `redlines.py` | Forbidden-path and forbidden-token scanner over source files |
| `render.py` | Orchestration layer: loads, validates, aggregates, scans, reports |
| `schemas.py` | DiagEvent and AnomalySummary schema validation |
| `__init__.py` | Package init with `__version__` |

This represents a monitoring and diagnostic sub-system. It is not a determinism primitive, not an artefact enforcement primitive, and not a test harness. It introduces I/O operations (`os.walk`, file reads/writes), external-facing data schemas, and orchestration logic.

**Verdict:** `prometheus/` is semantic expansion beyond the stated scope. It constitutes feature creep relative to the three defined work categories.

---

## 8. Missing Controls (Engineering Gaps)

| Control | Present | Location / Notes |
|---|---|---|
| Cryptographic signing beyond hash | No | Decision artefacts carry SHA-256 only. No HMAC, no RSA/ECDSA signature, no key material. |
| Append-only ledger | No | `commit_gate/reports/` holds per-decision JSON files. No append-only structure, no hash-chain, no tamper-evidence beyond the per-file `decision_hash`. |
| Multi-tenant isolation enforcement | No | `authority_scope` dict is a passthrough field. No per-tenant namespace enforcement or isolation boundary exists in `engine.py`. |
| Coverage metrics | No | No `pytest-cov`, no `.coveragerc`, no `pyproject.toml` coverage config. CI does not report or gate on coverage percentage. |
| Post-market monitoring hooks | No | `prometheus/` provides aggregation and fit-report, but no hooks, callbacks, or alerting sinks exist. `prometheus/agg/`, `prometheus/diag/`, `prometheus/reports/` are empty directories (`.gitkeep` only). |
| Incident reporting stubs | No | No incident record schema, no incident report writer, no stub functions for incident creation. |
| Formal verification gaps | No formal verification | No TLA+, Alloy, Coq, or property-based testing (Hypothesis) present. Tests are example-based only. |

---

## 9. Final State Classification

### Classification: STABILISING

### Justification

| Criterion | Status | File Reference |
|---|---|---|
| Core primitives implemented | Yes | `authority_gate.py`, `stop_machine.py`, `invariant_litmus.py` |
| Core primitives tested | Yes | `test_authority_gate.py`, `test_stop_machine.py`, `test_invariant_litmus.py` |
| CI matrix across Python versions | Yes (defined) | `.github/workflows/ci.yml`, `.github/workflows/commit_gate_ci.yml` |
| Determinism implementation | Yes | `commit_gate/src/commit_gate/canonicalise.py` |
| Artefact enforcement (commit gate) | Partial | `commit_gate/src/commit_gate/engine.py` — verdict produced but `invariant_hash` not validated, `timestamp_utc` not enforced |
| Golden hash regression tests | No | Absent from all test files |
| Replay demonstration | No | No fixture or test demonstrating replay |
| SUPERVISED verdict path | No | Only ALLOW, REFUSE, ESCALATE defined |
| Time-bound enforcement | No | `timestamp_utc` accepted but unused in enforcement |
| Coverage configuration | No | No coverage tooling present |
| Cryptographic signing | No | SHA-256 only |
| Append-only ledger | No | Flat file writes only |
| Formal verification | No | No property-based or formal methods |
| Stability log | 1 entry | `STABILITY_LOG.md` — 1 day recorded (2026-02-22) |

The repository has a functioning test matrix, determinism primitives, and CI enforcement guards. The commit gate produces verifiable artefacts. However, time-bound enforcement, evidence validation, replay demonstration, coverage reporting, and cryptographic signing are absent. The `prometheus/` module has expanded scope beyond the stated primitives. One day of stability is recorded.

The repository does not meet ENFORCEMENT-READY criteria. Classification is **STABILISING**.
