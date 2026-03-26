# PROOF_CARRYING_PACKET_SPEC_v1

**Artifact ID:** `PROOF_CARRYING_PACKET_SPEC_v1`
Foundation layer for proof-carrying execution governance.

**Depends on:** ADMISSIBILITY_ALGEBRA_v1
**FC Scope:** constraint-workshop
**Date:** 2026-03-26

---

## 0. Purpose

Define the structural requirements for proof-carrying action packets.

A packet without proof is not "untrusted" — it is **incomplete**.
No proof = no packet. No packet = no execution path.

This spec does not encode policy. It defines what must be proven before any action may execute.

---

## 1. Non-Goals

- Policy encoding or rule authoring
- Natural language justification
- Narrative explanation of intent
- Partial validation or "soft" proof
- Inference of missing claims
- Cross-packet proof inheritance

---

## 2. Packet Structure

A proof-carrying packet is the sole unit of execution request.

```
Packet {
  packet_id       : UUID
  schema_version  : SemVer
  actor_id        : ActorRef
  requested_action: ActionRef
  object_ref      : ObjectRef
  state_claim     : StateHash
  authority_claim : AuthorityToken
  dependencies    : List<DependencyRef>
  timestamp       : ISO8601
  nonce           : Bytes
  provenance      : ProvenanceTag
  payload_hash    : SHA256
  proof_bundle    : ProofBundle
}
```

No field is optional. A packet missing any field is malformed and rejected without evaluation.

---

## 3. Proof Bundle

The proof bundle is a structured set of machine-checkable claims attached to the packet.

```
ProofBundle {
  claims          : List<ProofClaim>
  witness_set     : MinimalWitnessSet
  bundle_hash     : SHA256
}
```

### 3.1 Proof Claims

Each claim is a single, verifiable assertion:

```
ProofClaim {
  claim_type  : ClaimType
  claim_value : Bytes
  evidence    : EvidenceRef
  scope       : ClaimScope
  freshness   : Timestamp
}
```

**Required claim types per action:**

Every registered action defines a **proof obligation set** — the exact set of claim types that must be present.

| Claim Type | Meaning |
|---|---|
| `OBJECT_EXISTS` | Target object is present in current state |
| `ACTOR_BOUND` | Actor is bound and valid for this context |
| `DEPENDENCY_SATISFIED` | Named dependency is resolved |
| `STATE_PRECONDITION_MATCH` | State hash matches expected precondition |
| `ACTION_REGISTERED` | Requested action exists in action registry |
| `POLICY_VERSION_MATCH` | Policy surface version matches current epoch |
| `AUTHORITY_FRESH` | Authority was computed at evaluation time |

### 3.2 Claim Validation Rules

1. Each claim must be independently verifiable
2. Each claim must reference exactly one evidence source
3. No claim may assert facts outside its declared scope
4. No claim may reference future state
5. Claims are not composable — each stands alone

---

## 4. Minimal Witness Set

For each action type, the system defines the **smallest set of facts** required for admissibility.

```
MinimalWitnessSet {
  action_type     : ActionRef
  required_claims : Set<ClaimType>
  witness_hash    : SHA256
}
```

**Invariant:** The witness set for a given action type is fixed per policy epoch. It cannot be extended, reduced, or overridden at evaluation time.

The minimal witness set is the proof. Nothing more. Nothing less.

---

## 5. Proof Semantics

### 5.1 Completeness Rule

```
For action A with witness set W:
  packet.proof_bundle.claims MUST cover every claim_type in W
  Missing any claim → packet is INCOMPLETE → verdict: HOLD
```

There is no partial credit.

### 5.2 Freshness Rule

```
For every claim C in proof_bundle:
  C.freshness MUST be within the current evaluation window
  Stale claim → packet is STALE → verdict: DENY
```

No cached proofs. No inherited proofs. No "it was valid earlier".

### 5.3 Scope Rule

```
For every claim C in proof_bundle:
  C.scope MUST match (actor, action, object, state) of the enclosing packet
  Scope mismatch → verdict: DENY
```

A proof for one context cannot be transplanted to another.

### 5.4 Minimality Rule

```
For action A with witness set W:
  packet.proof_bundle.claims MUST contain exactly |W| claims
  Extra claims → ignored (not evaluated, not trusted)
  Fewer claims → INCOMPLETE → verdict: HOLD
```

Proof is necessary and sufficient. Excess is noise.

---

## 6. Proof Evaluation Flow

```
PACKET received
  |
  v
STRUCTURAL CHECK — all fields present?
  | no  -> REJECT (malformed)
  | yes
  v
WITNESS SET LOOKUP — what claims does this action require?
  | action not registered -> DENY
  | found
  v
COMPLETENESS CHECK — all required claims present?
  | no  -> HOLD (incomplete)
  | yes
  v
FRESHNESS CHECK — all claims within evaluation window?
  | no  -> DENY (stale)
  | yes
  v
SCOPE CHECK — all claims scoped to this packet?
  | no  -> DENY (scope violation)
  | yes
  v
CLAIM VERIFICATION — each claim independently valid?
  | any invalid -> DENY (proof failure)
  | all valid
  v
CONTRADICTION CHECK — do claims contradict each other or state?
  | yes -> route to PARADOX_VECTOR
  | no
  v
FORWARD TO ADMISSIBILITY GATE
  -> verdict computed per ADMISSIBILITY_ALGEBRA_v1
```

---

## 7. Failure Conditions

| Condition | Verdict | Reason Code |
|---|---|---|
| Missing packet field | REJECT | `MALFORMED_PACKET` |
| Incomplete proof bundle | HOLD | `PROOF_INCOMPLETE` |
| Stale claim | DENY | `PROOF_STALE` |
| Scope mismatch | DENY | `PROOF_SCOPE_VIOLATION` |
| Invalid claim evidence | DENY | `PROOF_INVALID` |
| Contradictory claims | PARADOX | `PROOF_CONTRADICTION` |
| Extra claims beyond witness set | — | Ignored silently |
| Unregistered action | DENY | `ACTION_NOT_REGISTERED` |

---

## 8. Invariants

1. **No proof, no execution path.** A packet without a complete proof bundle cannot reach the admissibility gate.
2. **Proof cannot elevate authority.** No claim in the proof bundle can grant authority not already present.
3. **Proof cannot introduce objects.** No claim can assert the existence of objects not in current state.
4. **Proof cannot override the action registry.** Claims cannot make unregistered actions admissible.
5. **Proof is non-transferable.** A proof bundle is valid only for the exact (actor, action, object, state, time) tuple of its enclosing packet.
6. **Proof is non-replayable.** Nonce + timestamp + state_claim together prevent replay.
7. **Proof evaluation is deterministic.** Same packet + same state = same evaluation result. Always.
8. **Incomplete is not invalid — it is absent.** HOLD means "this packet does not yet exist as a valid request."
9. **Contradiction routes to Paradox Vector.** Contradictory proofs are not "wrong" — they are structurally impossible and handled per ADMISSIBILITY_ALGEBRA_v1 Section 6.
10. **Minimal witness sets are epoch-locked.** They change only when the policy epoch changes, never mid-evaluation.

---

## 9. Conformance Criteria

An implementation conforms to this spec if and only if:

1. Every action request is wrapped in a proof-carrying packet
2. Every packet is evaluated through the full proof evaluation flow (Section 6)
3. No packet with incomplete proof reaches the admissibility gate
4. No proof claim is inferred, interpolated, or assumed
5. Proof evaluation produces identical results for identical inputs
6. Stale, scoped, or invalid proofs produce DENY, not degraded execution
7. Contradiction detection routes to the Paradox Vector, not to error handling

---

## 10. Relationship to Other Specs

- **ADMISSIBILITY_ALGEBRA_v1:** This spec feeds into the admissibility gate. Proof evaluation is a prerequisite, not a replacement.
- **CANONICAL_PACKET_NORMAL_FORM_v1:** Defines the exact canonical representation of packets before proof evaluation.evaluation.
- **GOLDEN_CONFORMANCE_CORPUS_v1:** Includes proof-carrying packet test vectors with expected verdicts.

---

**END OF SPEC**
