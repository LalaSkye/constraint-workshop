---
mode: 'agent'
description: 'Intake prompt: generate schemas + golden test vectors for CommitBoundary v0 (no implementation).'
---

# CommitBoundary Spec Intake — v0

You are a specification author for the `constraint-workshop` repository.

## SCOPE CONSTRAINT — READ FIRST

You must generate **schemas and golden test vectors only**.
Do NOT generate any Python implementation classes, engine code, or runtime logic.
Do NOT create `BoundarySpec`, `BoundaryVerdict`, or any callable Python class.
Implementation is deferred to a separate, subsequent PR.

## Context

The repository contains deterministic control primitives (stdlib-only, no network, no randomness).
All decisions are fail-closed: missing policy → DENY; no Receipt possible → DENY;
self-approval → DENY; approval required but absent → HOLD (never ALLOW).

## What to generate

Produce exactly the following files as fenced code blocks with the path as the language label.

### 1. `spec/schemas/commit_boundary_spec.schema.json`

A JSON Schema (draft-07) describing a `BoundarySpec` document:
- `actor_id` (string, required)
- `action_classes` (array of strings, minItems 1, unique, required)
- `scope_paths` (array of strings, minItems 1, unique, required)
- `boundary_hash` (string, pattern `^[0-9a-f]{64}$`, required)

### 2. `spec/schemas/boundary_verdict.schema.json`

A JSON Schema (draft-07) describing a `BoundaryVerdict` document:
- `verdict` (string, enum `["WITHIN", "BREACH"]`, required)
- `actor_id` (string, required)
- `action_class` (string, required)
- `scope_paths_requested` (array of strings, required)
- `boundary_hash` (string, pattern `^[0-9a-f]{64}$`, required)

### 3. `spec/golden/build1/within.json`

A golden vector representing a **WITHIN** verdict:
- actor and action class exactly match the spec
- all requested scope_paths are in the spec's scope_paths
- Include a `"_comment"` field: `"Happy path: all fields match"`

### 4. `spec/golden/build1/breach_actor.json`

A golden vector representing a **BREACH** verdict caused by wrong `actor_id`.
- Include a `"_comment"` field: `"actor_id mismatch triggers BREACH"`

### 5. `spec/golden/build1/breach_action.json`

A golden vector representing a **BREACH** verdict caused by a disallowed `action_class`.
- Include a `"_comment"` field: `"action_class not in spec triggers BREACH"`

### 6. `spec/golden/build1/breach_scope.json`

A golden vector representing a **BREACH** verdict caused by an out-of-scope path.
- Include a `"_comment"` field: `"scope_path outside envelope triggers BREACH"`

### 7. `spec/golden/build2/hold_no_approval.json`

A golden vector representing a **HOLD** outcome:
- approval is required by the spec but no approval is present in the request
- Include a `"_comment"` field: `"approval required but absent -> HOLD, never ALLOW"`

### 8. `tests/test_schemas.py`

A `pytest` test file that:
- Loads `spec/schemas/commit_boundary_spec.schema.json` and `spec/schemas/boundary_verdict.schema.json` using only stdlib (`json`).
- Validates that each golden file in `spec/golden/build1/` and `spec/golden/build2/` is valid JSON (parseable).
- Checks that every golden verdict file contains a `"verdict"` key whose value is one of `["WITHIN", "BREACH", "HOLD"]`.
- Checks that every golden file contains a `"_comment"` key.
- Uses `jsonschema` if available, otherwise skips schema-validation tests with `pytest.importorskip`.

### 9. `tests/test_golden_invariants.py`

A `pytest` test file that encodes the hard decision invariants as parameterised checks against the golden vectors:
- For every golden file with `"verdict": "WITHIN"`: assert `actor_id`, `action_class`, and all `scope_paths_requested` are present and non-empty.
- For every golden file with `"verdict": "BREACH"`: assert at least one of actor, action, or scope is the cause (field `"breach_reason"` must be present).
- For `hold_no_approval.json`: assert `"verdict"` is `"HOLD"` and `"approval_present"` is `false`.
- No implementation logic — tests assert only the structure and values of the JSON golden files.

### 10. `README.md` section — append only

Append a new section at the end of the existing README with heading `## What is inspectable in v0`.

Content must include:
- One sentence stating that v0 ships schemas and golden test vectors only; implementation is in a future PR.
- A bullet list of the schema files under `spec/schemas/`.
- A bullet list of the golden vector files under `spec/golden/`.
- A bullet list of the test files and what invariant each covers.
- The sentence: "All verdicts are fail-closed: missing policy → DENY; no Receipt → DENY; self-approval → DENY; approval required but absent → HOLD."

## Output format

Return only fenced code blocks, one per file, with the relative file path as the fence label.
Do not add any prose, explanation, or commentary outside the code blocks.

