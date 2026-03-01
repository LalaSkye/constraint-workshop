# Verify — How to verify a commit gate decision artefact

All information sourced from repo code. No invented architecture.

## 1. Canonicalisation rules

Source: `commit_gate/src/commit_gate/canonicalise.py`

| Rule | Value |
|---|---|
| Encoding | UTF-8 |
| Key ordering | Sorted recursively (all levels) |
| Whitespace | None (no spaces, no newlines) |
| List ordering | Preserved as-is — **caller must pre-sort** |
| Hash algorithm | SHA-256 |
| Hash encoding | Lowercase hex string (64 characters) |

**Canonical JSON example** (actual output for the SAMPLE_REQUEST in tests):

```
{"action_class":"FILE","actor_id":"ricky","authority_scope":{"project":"alpha"},"context":{"description":"test commit"},"invariant_hash":"abc123"}
```

## 2. How `request_hash` is computed

Source: `commit_gate/src/commit_gate/engine.py` — `build_request_obj` + `canonical_hash`

1. Build a request object from these five fields (timestamp excluded):
   - `actor_id`
   - `action_class`
   - `context`
   - `authority_scope`
   - `invariant_hash`
2. Apply canonicalise (sorted keys, no whitespace, UTF-8).
3. SHA-256 hex digest of the resulting bytes.

```python
request_obj = {
    "actor_id": ...,
    "action_class": ...,
    "context": ...,
    "authority_scope": ...,
    "invariant_hash": ...,
}
request_hash = sha256(canonical_json(request_obj))
```

## 3. How `decision_hash` is computed

Source: `commit_gate/src/commit_gate/engine.py` — `evaluate`

1. Resolve verdict (`ALLOW` / `REFUSE` / `ESCALATE`) using the deterministic resolution order.
2. Collect and sort `reasons` lexicographically.
3. Build decision object:

```python
decision_obj = {
    "request": request_obj,   # same object as in request_hash
    "verdict": verdict,
    "reasons": sorted_reasons,
}
decision_hash = sha256(canonical_json(decision_obj))
```

The `decision_hash` commits to: the full request fields, the verdict, and the reasons list.

## 4. Verdict output schema (CommitVerdict)

The CLI and `evaluate()` both return canonical JSON with these fields:

| Field | Type | Notes |
|---|---|---|
| `verdict` | string | `ALLOW`, `REFUSE`, or `ESCALATE` |
| `reasons` | array of strings | Sorted lexicographically |
| `decision_hash` | string | 64-char lowercase SHA-256 hex |
| `request_hash` | string | 64-char lowercase SHA-256 hex |
| `artefact_version` | string | `"0.1"` |

Fields in canonical output are sorted alphabetically.

## 5. Resolution order (deterministic)

Source: `commit_gate/src/commit_gate/engine.py` docstring

```
1. Denylist match  => REFUSE  (reason: denylist_match)
2. Allowlist match => ALLOW   (reason: allowlist_match)
3. Escalation match => ESCALATE (reason: escalation_match)
4. Default         => REFUSE  (reason: default_refuse)
```

## 6. Scope matching rules

Source: `commit_gate/src/commit_gate/engine.py` — `_scope_matches`

- Exact string match only (no glob, no regex, no prefix).
- All keys in `rule.scope_match` must exist in `request.authority_scope` with identical values.
- Request may carry extra scope keys (superset is allowed).

## 7. Chain / genesis note

This implementation does not use a blockchain-style hash chain. Each verdict is a self-contained artefact. There is no `prev_hash` field and no GENESIS sentinel in the current v0.1 schema.

## 8. How to run the verifier CLI

Source: `commit_gate/src/commit_gate/cli.py`

### Evaluate a request

```bash
# from the repo root
python -m commit_gate evaluate \
  --request commit_gate/rules/request_example.json \
  --ruleset commit_gate/rules/ruleset.json
```

Or using the bundled ruleset with an inline request file:

```bash
cat > /tmp/request.json <<'EOF'
{
  "actor_id": "ricky",
  "action_class": "FILE",
  "context": {"description": "test commit"},
  "authority_scope": {"project": "alpha"},
  "invariant_hash": "abc123"
}
EOF

cd commit_gate
python -m commit_gate evaluate \
  --request /tmp/request.json \
  --ruleset rules/ruleset.json
```

### Detect authority drift

```bash
cd commit_gate
python -m commit_gate drift \
  --baseline baselines/authority_graph.json \
  --ruleset rules/ruleset.json \
  --invariant-hash abc123
```

## 9. Expected pass/fail outputs

### Evaluate — ALLOW (exit 0)

```json
{"artefact_version":"0.1","decision_hash":"09880c122bcec255c2964a28344496bca7b85e74fcb5180c304358beae5cc497","reasons":["allowlist_match"],"request_hash":"91be8e7594ee9fc3967632dce931884f6dbf357f58794fbca54b9e579fda447f","verdict":"ALLOW"}
```

Exit code: `0`

### Evaluate — REFUSE (exit 1)

```json
{"artefact_version":"0.1","decision_hash":"<sha256>","reasons":["default_refuse"],"request_hash":"<sha256>","verdict":"REFUSE"}
```

Exit code: `1`

### Drift — PASS (exit 0)

```json
{"added_edges":[],"pass":true,"reason":"no_expansion","removed_edges":[]}
```

Exit code: `0`

### Drift — FAIL (exit 1)

```json
{"added_edges":[["ricky","SIGN"]],"pass":false,"reason":"reachability_expansion_without_contract_revision","removed_edges":[]}
```

Exit code: `1`

## 10. Run existing determinism tests

```bash
cd commit_gate
python -m pytest tests/test_determinism.py -v
```

Expected: all 9 tests pass across Python 3.10, 3.11, 3.12.
