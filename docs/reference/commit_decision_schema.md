# Commit Decision Report — Envelope Schema

**schema_version:** `1.0`

## File naming

```
commit_decision_<commit_hash>.json
```

`commit_hash` is the SHA-256 hex digest of the canonical request object (the same value as `request_hash` in the internal verdict).

## Envelope fields

| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | string | ✓ | Schema version identifier (current: `"1.0"`) |
| `commit_hash` | string | ✓ | SHA-256 hex digest identifying the commit request |
| `decision` | string | ✓ | Gate outcome: `PASS`, `HOLD`, or `FAIL` |
| `reason_codes` | array of strings | ✓ | Sorted list of reason code tokens |

## `decision` values

| Value | Meaning |
|---|---|
| `PASS` | Request approved (allowlist match) |
| `HOLD` | Request escalated for review |
| `FAIL` | Request refused (denylist match or no rule match) |

## `reason_codes` families

| Code | Family |
|---|---|
| `allowlist_match` | Explicit allow |
| `denylist_match` | Explicit deny |
| `escalation_match` | Escalation required |
| `default_refuse` | No matching rule |

## Serialisation

The file is written as canonical JSON:
- Keys sorted lexicographically (recursive)
- No whitespace (`separators=(',', ':')`)
- UTF-8 encoding

## Example

```json
{"commit_hash":"a3f…","decision":"PASS","reason_codes":["allowlist_match"],"schema_version":"1.0"}
```
