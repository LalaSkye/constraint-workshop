# Commit Gate Engine v0.1

Deterministic commit authority gate. Converts commit authority from prose into a mechanically verifiable, hash-bound artefact.

## Contract

**Verdicts:** `ALLOW` | `REFUSE` | `ESCALATE`

**Resolution order (deterministic):**
1. Denylist match => `REFUSE`
2. Allowlist match => `ALLOW`
3. Escalation match => `ESCALATE`
4. Default => `REFUSE`

## Input (CommitRequest)

| Field | Type | Notes |
|---|---|---|
| actor_id | string | Plain string, no hierarchy |
| action_class | string | e.g. FILE, SEND, SIGN, DEPLOY |
| context | object | Minimal, canonicalised |
| authority_scope | object | Flat string->string only |
| invariant_hash | string | SHA256 of declared contract |
| timestamp_utc | string | Audit only, excluded from hashes |

## Output (CommitVerdict)

| Field | Type |
|---|---|
| verdict | ALLOW / REFUSE / ESCALATE |
| reasons | [string] (sorted) |
| decision_hash | sha256(request + verdict + reasons) |
| request_hash | sha256(canonical_request) |
| artefact_version | "0.1" |

## Scope matching

- Exact match only (no glob/regex/prefix)
- Rule scope_match keys must exist in request authority_scope
- Values must be identical strings
- Request may contain extra keys (superset allowed)

## Authority drift detection

- Builds authority graph from allowlist edges
- Compares baseline vs current graph
- New edges + unchanged invariant_hash => **FAIL**
- Removed edges => **PASS**
- New edges + changed invariant_hash + acknowledgement => **PASS**

## Usage

```bash
python -m commit_gate evaluate --request request.json --ruleset rules/ruleset.json
python -m commit_gate drift --baseline baselines/authority_graph.json --ruleset rules/ruleset.json --invariant-hash <hash>
```

## Tests

```bash
cd commit_gate
python -m pytest tests/ -v
```

## Constraints

- stdlib only
- No network
- Deterministic across Python 3.10/3.11/3.12
- No governance primitives beyond {ALLOW, REFUSE, ESCALATE}
- No coupling with /prometheus/ or other modules
