# OUTSTANDING_WORK_RISK_REPORT.md

**ARTEFACT_CLASS:** AUDIT_REPORT  
**TIMESTAMP:** 2026-03-01T00:00:00Z  
**SCOPE:** constraint-workshop repository — read-only evidence audit  
**STATUS:** PENDING_AUTHORITY_DECISION  
**VERSION:** 1.0  

---

## 1. PURPOSE

This document maps what the repository **currently proves** against what it **does not yet prove**, identifies outstanding gaps and governance decision points, and records recommended next actions. No code was modified to produce this report.

---

## 2. WHAT THE REPOSITORY CURRENTLY PROVES

### 2.1 Determinism

| Claim | Evidence | Strength |
|-------|----------|----------|
| `canonicalise()` is deterministic | Sorted-key JSON, UTF-8, no whitespace (`canonicalise.py`) | Code inspection |
| `canonical_hash()` is SHA-256 lower-case hex | `canonicalise.py` | Code inspection |
| Same input → byte-identical output in multi-iteration test | `test_determinism.py::test_t1_determinism` | Weak (relative; no pinned value) |
| Hash is stable across calls in same process | `test_determinism.py::test_t2_hash_stability` | Weak (relative; no pinned value) |
| Key ordering is stable regardless of insertion order | `test_determinism.py::test_t3_ordering` | Weak (relative) |

**Gap:** There is no *golden hash regression* test pinning an absolute expected digest for a known input. Multi-iteration tests detect regressions only within a single run on one Python version — they do not prevent silent hash drift between interpreter versions, upgrades to the `json` module, or encoding changes.

### 2.2 Decision Record / Evidentiary Artefact

| Claim | Evidence | Strength |
|-------|----------|----------|
| `evaluate()` returns verdict, reasons, decision_hash, request_hash, artefact_version | `engine.py` + all verdict tests | Present |
| ALLOW path tested | `test_determinism.py::test_verdict_allow` | Present |
| REFUSE (denylist) path tested | `test_determinism.py::test_verdict_refuse_denylist` | Present |
| REFUSE (default) path tested | `test_determinism.py::test_verdict_default_refuse` | Present |
| ESCALATE path tested | `test_determinism.py::test_verdict_escalate` | Present |
| `timestamp_utc` enforced (staleness/expiry) | — | **ABSENT** |
| `invariant_hash` validated against a known contract value | — | **ABSENT** |
| Replay demonstration (same input → same decision_hash, pinned) | — | **ABSENT** |

**Gap A:** `timestamp_utc` is accepted in `commit_request` (docstring documents it) but `evaluate()` makes no use of it. Any compliance claim that relies on time-bounded request validity is currently unsupported in code.

**Gap B:** `invariant_hash` is recorded in the request object and included in hash computation, but there is no check that it equals a known/expected contract value. A caller can pass any string and it will be hashed without validation.

**Gap C:** No test proves that replaying a specific fixed input fixture produces an *identical pinned decision_hash* value. This is the strongest form of determinism evidence and is currently absent.

### 2.3 Authority Drift Detection

| Claim | Evidence | Strength |
|-------|----------|----------|
| Reachability expansion detected without contract revision | `test_drift.py::test_t4_…` | Present |
| Tightening passes | `test_drift.py::test_t5_…` | Present |
| Acknowledged expansion with hash change passes | `test_drift.py::test_t6_…` | Present |
| Non-acknowledged expansion with hash change fails | `test_drift.py::test_t6_…_negative` | Present |

### 2.4 CI / Workflow Integrity

| Claim | Evidence | Strength |
|-------|----------|----------|
| Tests run across Python 3.10 / 3.11 / 3.12 | `ci.yml` matrix | Present (requires CI approval to run) |
| Binary artefacts (`__pycache__`, `.pyc`) blocked | `ci.yml` guard | Present |
| Protected files (`authority_gate.py`, `stop_machine.py`, `commit_gate/**`) modification blocked | `ci.yml` guard | Present |

**Gap:** `commit_gate/` and `prometheus/` are not installed as packages — tests rely on `sys.path.insert()` at the top of each test file. This is fragile: test results depend on the working directory and path resolution, not on properly installed code. A `pyproject.toml` or `setup.py` with `pip install -e .` would make imports reliable and standard.

**Gap:** No coverage gating. There is no `pytest-cov` integration and no minimum coverage threshold. Tests could silently under-exercise code paths.

---

## 3. WHAT THE REPOSITORY DOES NOT PROVE

| Missing Evidence | Risk if Left Open |
|-----------------|-------------------|
| Golden hash regression (pinned absolute digest for a fixed input) | Silent hash drift is undetectable across Python upgrades |
| Replay demonstration (fixed fixture → pinned decision_hash) | Cannot claim audit-trail reproducibility |
| `timestamp_utc` staleness enforcement | Compliance claims referencing time-bounded requests are unsupported |
| `invariant_hash` contract validation | Field is present in the artefact but does not constrain caller behaviour |
| `SUPERVISED` verdict | EU-AI-Act or equivalent mappings that claim SUPERVISED oversight cannot be satisfied — only `ESCALATE` exists |
| Coverage measurement | Unknown which code paths are exercised |
| Proper packaging | Import reliability depends on working directory; fragile in CI |

---

## 4. TERMINOLOGY MISMATCH

The codebase defines three verdicts: `ALLOW`, `REFUSE`, `ESCALATE`.

`ESCALATE` is the human-oversight / supervised path. There is **no** `SUPERVISED` verdict. Any external documentation, compliance mapping, or governance artefact that references `SUPERVISED` as a verdict is **inaccurate** against the current implementation.

**Decision required (D3):** Decide whether `ESCALATE` is the canonical term for the supervised outcome, or whether a separate `SUPERVISED` verdict should be added. Until resolved, avoid using `SUPERVISED` in any compliance mapping artefact.

---

## 5. PROMETHEUS SCOPE

The `prometheus/` subsystem provides:
- Event ingestion (JSONL)
- Schema validation
- Redline / forbidden-token scanning
- Aggregation and fit reports
- Hashing utilities

This is **monitoring and diagnostics** functionality. The stated scope of `constraint-workshop` is *deterministic control primitives*. Prometheus expands that scope into observability tooling.

**Decision required (D2):** Choose one:

| Option | Action |
|--------|--------|
| **A — Accept in-scope** | Document Prometheus as an intentional monitoring/diagnostics component in `README.md` and `docs/` |
| **B — Declare out-of-scope** | Move `prometheus/` to a separate repository or branch |
| **C — Label experimental** | Keep but add a clear `EXPERIMENTAL / NON-PRIMITIVE` label in `prometheus/README.md` |

Until a decision is recorded, Prometheus remains an undeclared scope expansion.

---

## 6. OUTSTANDING GOVERNANCE DECISIONS

| ID | Decision | Options | Status |
|----|----------|---------|--------|
| D1 | CI protection boundary: should `commit_gate/tests/**` and `commit_gate/baselines/**` be modifiable without CI failure? | Accept current `commit_gate/` boundary (tests require separate authorisation) OR narrow to `commit_gate/src/` | **OPEN** |
| D2 | Prometheus scope | In-scope / Out-of-scope / EXPERIMENTAL | **OPEN** |
| D3 | Terminology: `ESCALATE` vs `SUPERVISED` | Keep `ESCALATE` as canonical / Add `SUPERVISED` | **OPEN** |
| D4 | Enforce `timestamp_utc` staleness | Implement fail-closed enforcement / Remove from documented fields / Keep as recorded-only | **OPEN** |
| D5 | Enforce `invariant_hash` against contract | Implement validation / Remove from enforcement claims / Keep as recorded-only | **OPEN** |

---

## 7. RECOMMENDED NEXT ACTIONS

These are mechanical, minimal actions. Each requires explicit authority sign-off before implementation:

| ID | Action | Prerequisite | Risk |
|----|--------|-------------|------|
| R1 | Add golden hash regression test (pinned digest for a known fixture) | D1 resolved (tests/baselines accessible) | Low — evidence only, no semantic change |
| R2 | Add replay fixture + test (fixed request → pinned decision_hash) | D1 resolved | Low — evidence only |
| R3 | Implement `timestamp_utc` staleness enforcement in `evaluate()` | D4 decision recorded | **Medium — changes enforcement semantics** |
| R4 | Implement `invariant_hash` contract validation | D5 decision recorded | **Medium — changes enforcement semantics** |
| R5 | Add `pyproject.toml` / packaging for `commit_gate/` and `prometheus/` | None | Low — removes sys.path fragility |
| R6 | Add `pytest-cov` and coverage gate to CI | None | Low — adds visibility |
| R7 | Resolve Prometheus scope; label or move | D2 decision recorded | Low |
| R8 | Align terminology (ESCALATE vs SUPERVISED) in all docs and compliance artefacts | D3 decision recorded | Low |

---

## 8. FAILURE MODES TO WATCH

1. **Compliance claims from recorded-but-not-enforced fields.** `timestamp_utc` and `invariant_hash` appear in the request and decision record. They are not validated. A compliance artefact that asserts time-bounded or contract-validated decisions is unsupported by the current code.

2. **SUPERVISED claimed, only ESCALATE exists.** Any documentation or mapping that uses `SUPERVISED` as a verdict outcome is inaccurate until the D3 decision is made and implemented.

3. **Scope creep via Prometheus without governance declaration.** The `prometheus/` directory represents monitoring capability that is not a constraint primitive. Without a recorded scope decision, its inclusion cannot be defended in an audit.

4. **Silent hash drift.** Multi-iteration tests confirm internal consistency but do not pin absolute expected values. A change to the Python standard library `json` module or `hashlib` behaviour across versions could silently change hash output; there is no test that would catch this.

5. **Fragile CI due to sys.path hacks.** Tests in `commit_gate/tests/` and `prometheus/tests/` all use `sys.path.insert()`. If the working directory changes, or tests are run from a different location, imports may fail silently or pick up wrong modules.

---

## 9. STOP CONDITIONS (active)

The following actions **must not** proceed without explicit human authority sign-off:

- Any merge that changes enforcement semantics (`timestamp_utc` gating, `invariant_hash` validation, verdict enumeration)
- Any merge that changes the CI protection boundary (`commit_gate/**` → `commit_gate/src/**` or any other narrowing)
- Any compliance or governance artefact claiming `SUPERVISED` verdict support
- Any Prometheus integration into external systems before the D2 scope decision is recorded

---

## 10. AUDIT METHODOLOGY

This report was produced by:
1. Reading all source files under `commit_gate/src/`, `prometheus/src/`, root-level `.py` files
2. Reading all test files under `commit_gate/tests/` and `prometheus/tests/`
3. Reading `.github/workflows/ci.yml` and `.github/workflows/commit_gate_ci.yml`
4. Reading `ENGINEERING_STATUS.yaml`, `STABILITY_LOG.md`, `docs/`, `commit_gate/README.md`, `prometheus/README.md`
5. Running the test suite locally to confirm: **81 tests pass, 0 failures**

**No code was modified to produce this report.**

---

*END OF REPORT*
