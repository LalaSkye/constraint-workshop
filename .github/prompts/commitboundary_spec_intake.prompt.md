---
mode: 'agent'
description: 'Intake prompt: generate a v0 specification for the CommitBoundary primitive.'
---

# CommitBoundary Spec Intake — v0

You are a specification author for the `constraint-workshop` repository.
Your task is to produce a complete, self-contained v0 specification for a new primitive called **CommitBoundary**.

## Context

The repository already contains:
- `stop_machine` — a three-state deterministic machine (GREEN → AMBER → RED).
- `authority_gate` — an evidence-ordered access gate (NONE < USER < OWNER < ADMIN).
- `invariant_litmus` — a posture classifier (HARD_INVARIANT / COST_CURVE / EDGE).
- `commit_gate` — a hash-bound commit authority engine (ALLOW / REFUSE / ESCALATE).

All primitives share these invariants:
- stdlib only, no network, no randomness, no global state.
- Deterministic: same inputs → same outputs.
- Testable in complete isolation.

## CommitBoundary definition

A **CommitBoundary** is a declarative, hash-bound envelope that wraps a single logical
commit action and asserts:

1. **Scope envelope** — the set of resource paths or identifiers the commit is permitted to touch.
2. **Actor binding** — which actor (by `actor_id`) owns this boundary instance.
3. **Action class constraint** — which `action_class` values are permitted inside this boundary.
4. **Boundary hash** — SHA-256 of the canonical (sorted, minified) JSON representation of fields 1–3.
   Any mutation to scope, actor, or action constraints must produce a new hash.
5. **Violation detection** — given a `CommitRequest`, return `WITHIN` if the request is fully
   contained by the boundary, or `BREACH` if any field falls outside the declared envelope.

## What to generate

Produce the following files. Output each file as a fenced code block with its path as the language tag.

### 1. `commit_boundary/README.md`

Include:
- One-paragraph description.
- Invariants table (at minimum: boundary_hash immutability, WITHIN/BREACH are the only verdicts,
  scope matching is exact-string only, no side effects).
- Input/output field tables for `BoundarySpec` and `BoundaryVerdict`.
- Minimal usage example (Python snippet).
- How to run tests.

### 2. `commit_boundary/src/commit_boundary/__init__.py`

Export: `BoundarySpec`, `BoundaryVerdict`, `CommitBoundary`.

### 3. `commit_boundary/src/commit_boundary/boundary.py`

Implement:
- `BoundarySpec(actor_id, action_classes, scope_paths)` — immutable dataclass.
  - `boundary_hash: str` — computed at construction, SHA-256 hex of canonical JSON.
- `BoundaryVerdict` — enum with `WITHIN` and `BREACH`.
- `CommitBoundary(spec: BoundarySpec)` — evaluator class.
  - `evaluate(request: dict) -> BoundaryVerdict` — pure, no side effects.
    - Returns `BREACH` if `request["actor_id"] != spec.actor_id`.
    - Returns `BREACH` if `request["action_class"] not in spec.action_classes`.
    - Returns `BREACH` if any path in `request.get("scope_paths", [])` is not in `spec.scope_paths`.
    - Returns `WITHIN` otherwise.
- Canonicalisation: sort all collections before hashing; use `json.dumps(..., sort_keys=True, separators=(',',':'))`.

### 4. `commit_boundary/tests/test_boundary.py`

Cover all invariants with `pytest` tests:
- `WITHIN` verdict for a fully matching request.
- `BREACH` for wrong `actor_id`.
- `BREACH` for disallowed `action_class`.
- `BREACH` for out-of-scope path.
- Hash immutability: same spec constructed twice has the same `boundary_hash`.
- Hash sensitivity: mutating any spec field changes `boundary_hash`.
- No side effects: calling `evaluate()` does not mutate the spec.

## Constraints

- stdlib only (`hashlib`, `json`, `dataclasses`, `enum`).
- No new verdict values beyond `WITHIN` and `BREACH`.
- Scope matching: exact string match, no glob, no regex.
- `boundary_hash` must be 64-character lowercase hex SHA-256.
- Must be deterministic across Python 3.10, 3.11, 3.12.
- Do not import anything from `commit_gate`, `stop_machine`, `authority_gate`,
  `invariant_litmus`, or `prometheus`.

## Output format

Return only the file contents as fenced code blocks (path as the fence language label).
Do not add prose outside the code blocks.
