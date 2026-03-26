# GOLDEN_CONFORMANCE_CORPUS_v1

**Artifact ID:** `GOLDEN_CONFORMANCE_CORPUS_v1`
Canonical test corpus for conformance verification.

**Depends on:** ADMISSIBILITY_ALGEBRA_v1, PROOF_CARRYING_PACKET_SPEC_v1, CANONICAL_PACKET_NORMAL_FORM_v1
**FC Scope:** constraint-workshop
**Date:** 2025-03-26

---

## 0. Purpose

Define the reference test corpus against which any implementation must produce identical verdicts.

If two systems produce different verdicts for the same canonical corpus, they are not equivalent.

This is the conformance surface. This is where imitators fail.

---

## 1. Non-Goals

- Exhaustive fuzzing or property-based testing
- Performance benchmarking
- Implementation guidance or tutorials
- Coverage of application-specific policies
- Stress testing or load simulation

---

## 2. Corpus Structure

The corpus is organised into test vectors. Each vector is a self-contained unit:

```
TestVector {
  vector_id        : String
  category         : TestCategory
  description      : String
  input_packet     : CanonicalPacket
  system_state     : StateSnapshot
  action_registry  : ActionRegistrySnapshot
  policy_epoch     : EpochRef
  expected_verdict : Verdict
  expected_reason  : ReasonCode
  expected_route   : Route  // ADMISSIBILITY_GATE | PARADOX_VECTOR | REJECT
}
```

---

## 3. Test Categories

### 3.1 Valid Packets (ALLOW expected)

| Vector ID | Description |
|---|---|
| `VALID-001` | Minimal valid packet with complete proof bundle |
| `VALID-002` | Valid packet with multiple satisfied dependencies |
| `VALID-003` | Valid packet at epoch boundary (exact match) |
| `VALID-004` | Valid packet with empty dependency list |
| `VALID-005` | Valid packet with maximum witness set |

### 3.2 Malformed Packets (REJECT expected)

| Vector ID | Description |
|---|---|
| `MALFORM-001` | Missing packet_id field |
| `MALFORM-002` | Missing proof_bundle entirely |
| `MALFORM-003` | Null value in required field |
| `MALFORM-004` | Duplicate field names |
| `MALFORM-005` | Extra field not in schema |
| `MALFORM-006` | Non-UTF-8 encoded string |
| `MALFORM-007` | Uppercase hex in state_claim hash |
| `MALFORM-008` | Timestamp with timezone offset (not Z) |
| `MALFORM-009` | Unsorted dependencies list |
| `MALFORM-010` | payload_hash length != 64 |

### 3.3 Incomplete Proof (HOLD expected)

| Vector ID | Description |
|---|---|
| `INCOMPLETE-001` | Proof bundle missing one required claim |
| `INCOMPLETE-002` | Proof bundle with zero claims |
| `INCOMPLETE-003` | Proof bundle missing ACTOR_BOUND claim |
| `INCOMPLETE-004` | Proof bundle missing STATE_PRECONDITION_MATCH |
| `INCOMPLETE-005` | Proof bundle with wrong number of claims for action type |

### 3.4 Stale Proof (DENY expected)

| Vector ID | Description |
|---|---|
| `STALE-001` | Claim freshness outside evaluation window |
| `STALE-002` | Authority claim from previous epoch |
| `STALE-003` | State_claim hash from prior state |
| `STALE-004` | All claims fresh except one |
| `STALE-005` | Timestamp in future (beyond evaluation window) |

### 3.5 Scope Violations (DENY expected)

| Vector ID | Description |
|---|---|
| `SCOPE-001` | Claim scoped to different actor |
| `SCOPE-002` | Claim scoped to different object |
| `SCOPE-003` | Claim scoped to different action |
| `SCOPE-004` | Claim scoped to different state |
| `SCOPE-005` | Mixed scope claims (some valid, some not) |

### 3.6 Authority Violations (DENY expected)

| Vector ID | Description |
|---|---|
| `AUTH-001` | No authority present, commit requested |
| `AUTH-002` | Authority for wrong actor |
| `AUTH-003` | Authority for wrong action type |
| `AUTH-004` | Expired authority token |
| `AUTH-005` | Authority claim attempts privilege escalation |

### 3.7 Contradiction Packets (PARADOX_VECTOR expected)

| Vector ID | Description |
|---|---|
| `PARADOX-001` | Object absent + modify requested |
| `PARADOX-002` | Actor unbound + privileged action claimed |
| `PARADOX-003` | State hash mismatch + transition requested |
| `PARADOX-004` | Dependency unresolved + execution demanded |
| `PARADOX-005` | Claims assert mutually exclusive states |
| `PARADOX-006` | Authority contradicts actor binding |

### 3.8 Replay Attacks (DENY expected)

| Vector ID | Description |
|---|---|
| `REPLAY-001` | Exact duplicate of previously executed packet |
| `REPLAY-002` | Same packet with incremented timestamp only |
| `REPLAY-003` | Same nonce reused with different payload |
| `REPLAY-004` | Valid packet replayed after state transition |

### 3.9 Registry Violations (DENY expected)

| Vector ID | Description |
|---|---|
| `REGISTRY-001` | Action not in action registry |
| `REGISTRY-002` | Action removed from registry between epochs |
| `REGISTRY-003` | Unknown action type with valid proof bundle |

### 3.10 Canonicalisation Equivalence

| Vector ID | Description |
|---|---|
| `CANON-001` | Two packets, different field order, same semantics → same canonical form |
| `CANON-002` | Two packets, different whitespace, same semantics → same canonical form |
| `CANON-003` | Two packets, different list ordering, same semantics → same canonical form |
| `CANON-004` | Two packets, different timestamp format (offset vs Z), only Z is valid |
| `CANON-005` | Packet with uppercase hex vs lowercase hex → normalised to same form |

---

## 4. Verdict Registry

Each test vector specifies exactly one expected verdict and reason code.

```
ExpectedResult {
  verdict     : {ALLOW, DENY, HOLD, REJECT, PARADOX}
  reason_code : ReasonCode
  route       : {ADMISSIBILITY_GATE, PARADOX_VECTOR, REJECT_EARLY}
}
```

No ambiguity. No "acceptable alternatives". One input, one verdict.

---

## 5. Conformance Rules

### 5.1 Syntax Conformance

The implementation must correctly parse and normalise every test vector packet per CANONICAL_PACKET_NORMAL_FORM_v1.

### 5.2 Semantic Conformance

The implementation must produce the exact expected verdict and reason code for every test vector.

### 5.3 Temporal Conformance

The implementation must correctly evaluate freshness windows, epoch boundaries, and stale claims.

### 5.4 Refusal Conformance

The implementation must refuse (DENY/HOLD/REJECT) every test vector that is expected to be refused. No false accepts.

### 5.5 Determinism Conformance

Running any test vector N times must produce identical results every time.

---

## 6. Diff Protocol

When comparing two implementations against the corpus:

```
For each test vector V:
  result_A = implementation_A.evaluate(V.input_packet, V.system_state)
  result_B = implementation_B.evaluate(V.input_packet, V.system_state)
  if result_A != result_B:
    record DIVERGENCE(V.vector_id, result_A, result_B)
```

Any divergence means the implementations are not equivalent.

---

## 7. Corpus Versioning

- The corpus is versioned alongside the specs it depends on
- Adding test vectors increments MINOR version
- Changing expected verdicts increments MAJOR version
- Removing test vectors is forbidden (append-only)
- Each vector is immutable once published

---

## 8. Invariants

1. **One input, one verdict.** Every test vector has exactly one correct answer.
2. **Corpus is append-only.** Vectors are never removed or modified.
3. **Verdicts are deterministic.** No test vector may have multiple acceptable outcomes.
4. **Full coverage of failure modes.** Every failure condition defined in PROOF_CARRYING_PACKET_SPEC_v1 Section 7 has at least one test vector.
5. **Contradiction coverage.** Every contradiction class from ADMISSIBILITY_ALGEBRA_v1 has at least one test vector.
6. **Canonicalisation coverage.** Every forbidden representation from CANONICAL_PACKET_NORMAL_FORM_v1 Section 9 has at least one test vector.

---

## 9. Conformance Criteria

An implementation conforms to the golden corpus if and only if:

1. It produces the correct verdict for every test vector
2. It produces the correct reason code for every test vector
3. It routes to the correct handler (admissibility gate, paradox vector, or early reject) for every test vector
4. It produces identical results on repeated execution
5. It passes all canonicalisation equivalence tests

---

## 10. Relationship to Other Specs

- **ADMISSIBILITY_ALGEBRA_v1:** Contradiction classes and verdict algebra are tested here.
- **PROOF_CARRYING_PACKET_SPEC_v1:** Proof evaluation flow and failure conditions are tested here.
- **CANONICAL_PACKET_NORMAL_FORM_v1:** Normalisation and equivalence rules are tested here.

---

**END OF SPEC**
