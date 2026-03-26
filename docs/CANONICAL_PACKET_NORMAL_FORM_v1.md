# CANONICAL_PACKET_NORMAL_FORM_v1

**Artifact ID:** `CANONICAL_PACKET_NORMAL_FORM_v1`
Formal specification for canonical packet representation.

**Depends on:** ADMISSIBILITY_ALGEBRA_v1, PROOF_CARRYING_PACKET_SPEC_v1
**FC Scope:** constraint-workshop
**Date:** 2025-03-26

---

## 0. Purpose

Define the one and only canonical representation for every packet before evaluation.

Every input packet must reduce to exactly one canonical form. Two semantically equivalent packets must produce identical canonical representations. No ambiguity survives canonicalisation.

---

## 1. Non-Goals

- Human-readable formatting
- Pretty-printing or display logic
- Lossy compression or summarisation
- Format negotiation or content-type flexibility
- Backward-compatible encoding of legacy formats

---

## 2. Core Invariant

```
For any two packets P1 and P2:
  semantically_equivalent(P1, P2) iff canonical(P1) == canonical(P2)
```

This is the only invariant that matters. Everything else follows from it.

---

## 3. Canonical Field Order

All packet fields must appear in the following fixed order:

```
1.  packet_id
2.  schema_version
3.  actor_id
4.  requested_action
5.  object_ref
6.  state_claim
7.  authority_claim
8.  dependencies
9.  timestamp
10. nonce
11. provenance
12. payload_hash
13. proof_bundle
```

No reordering. No omission. No insertion of additional fields.

A packet with fields in any other order is not canonical and must be normalised before evaluation.

---

## 4. Encoding Rules

### 4.1 String Encoding

- All strings: UTF-8, no BOM
- No trailing whitespace
- No leading whitespace in values
- Null bytes forbidden

### 4.2 Numeric Encoding

- No leading zeros
- No trailing decimal points
- No scientific notation
- Integer values must not contain decimal points

### 4.3 List Encoding

- Lists are ordered deterministically
- `dependencies`: sorted lexicographically by DependencyRef string
- `proof_bundle.claims`: sorted lexicographically by claim_type string
- Empty lists are encoded as empty arrays, never null

### 4.4 Hash Encoding

- All hashes: lowercase hexadecimal
- SHA256 only
- No prefix (no "0x", no "sha256:")
- Exactly 64 characters

### 4.5 Timestamp Encoding

- ISO 8601 UTC only
- Format: `YYYY-MM-DDTHH:MM:SS.fffZ`
- Always millisecond precision
- Always Z suffix (no timezone offsets)

### 4.6 Null Handling

- Null is forbidden in canonical form
- Every field must have a value
- "Absent" is not expressible — missing fields make the packet malformed

---

## 5. Serialisation

### 5.1 Canonical Serialisation Format

- JSON
- Keys unquoted: no (standard JSON quoting)
- No whitespace between tokens (compact form)
- No trailing comma
- No comments
- Deterministic key order (Section 3)

### 5.2 Canonical Hash Computation

```
canonical_hash(packet) = SHA256(canonical_json_bytes(packet))
```

Where `canonical_json_bytes` produces the compact JSON with deterministic field ordering as defined above, encoded as UTF-8 bytes.

---

## 6. Normalisation Process

Any incoming packet must pass through normalisation before evaluation:

```
RAW PACKET received
  |
  v
FIELD PRESENCE CHECK — all 13 fields present?
  | no  -> REJECT (malformed)
  | yes
  v
TYPE CHECK — each field matches expected type?
  | no  -> REJECT (type violation)
  | yes
  v
FIELD REORDER — sort to canonical order (Section 3)
  |
  v
VALUE NORMALISATION — apply encoding rules (Section 4)
  |
  v
LIST SORT — sort all list fields deterministically
  |
  v
PROOF BUNDLE NORMALISATION — sort claims by claim_type
  |
  v
COMPACT SERIALISE — produce canonical JSON
  |
  v
HASH — compute canonical_hash
  |
  v
VERIFY payload_hash == canonical_hash of payload
  | mismatch -> DENY (integrity violation)
  | match
  v
CANONICAL PACKET ready for proof evaluation
```

---

## 7. Type Constraints

| Field | Type | Constraint |
|---|---|---|
| `packet_id` | UUID v4 | Lowercase, hyphenated |
| `schema_version` | SemVer | `MAJOR.MINOR.PATCH` only |
| `actor_id` | String | Non-empty, no whitespace |
| `requested_action` | String | Must exist in action registry |
| `object_ref` | String | Non-empty, no whitespace |
| `state_claim` | SHA256 hex | 64 chars, lowercase |
| `authority_claim` | String | Non-empty |
| `dependencies` | List<String> | Sorted, may be empty |
| `timestamp` | ISO8601 | UTC, millisecond precision |
| `nonce` | Hex string | Even length, lowercase |
| `provenance` | String | Non-empty |
| `payload_hash` | SHA256 hex | 64 chars, lowercase |
| `proof_bundle` | ProofBundle | As defined in PROOF_CARRYING_PACKET_SPEC_v1 |

---

## 8. Equivalence Rules

Two packets are semantically equivalent if and only if their canonical forms are byte-identical.

There is no "close enough". There is no fuzzy matching. There is no similarity score.

```
equivalent(P1, P2) iff canonical_bytes(P1) == canonical_bytes(P2)
```

---

## 9. Forbidden Representations

The following representations are explicitly forbidden and must cause rejection:

1. Fields in non-canonical order
2. Duplicate fields
3. Null values for any field
4. Whitespace in compact serialisation
5. Non-UTF-8 encoding
6. Uppercase hex in hashes
7. Timezone offsets in timestamps (must be Z)
8. Unsorted list elements
9. Extra fields not in the schema
10. Missing fields

Any of these in a raw packet triggers normalisation. Any of these after normalisation triggers REJECT.

---

## 10. Invariants

1. **One packet, one form.** Every valid packet has exactly one canonical representation.
2. **Semantic equivalence = byte equivalence.** No interpretation layer between canonical form and comparison.
3. **Normalisation is idempotent.** `canonical(canonical(P)) == canonical(P)`
4. **Canonicalisation never changes semantics.** It changes representation only.
5. **No optional structure.** The canonical form is fully determined by the field values.
6. **Hash integrity.** The canonical hash is computed over the canonical JSON bytes. Any mutation is detectable.
7. **Format is epoch-stable.** The canonical format changes only when schema_version changes.

---

## 11. Conformance Criteria

An implementation conforms to this spec if and only if:

1. All packets are normalised before evaluation
2. Normalisation produces identical output for semantically equivalent inputs
3. Canonical hash is computed per Section 5.2
4. Forbidden representations (Section 9) are detected and handled
5. No evaluation occurs on non-canonical packets
6. Equivalence is determined by byte comparison of canonical forms only

---

## 12. Relationship to Other Specs

- **ADMISSIBILITY_ALGEBRA_v1:** Canonical packets are the input to the admissibility gate.
- **PROOF_CARRYING_PACKET_SPEC_v1:** Proof bundles within packets follow their own canonicalisation (claims sorted by type).
- **GOLDEN_CONFORMANCE_CORPUS_v1:** (forthcoming) Will include canonical form test vectors and equivalence test pairs.

---

**END OF SPEC**
