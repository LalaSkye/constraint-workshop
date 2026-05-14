# PQC Crypto Posture Receipt Schema Extension

**Version:** 0.1  
**Status:** DRAFT  
**Normativity:** NORMATIVE  
**Scope:** Interface-only schema extension — no runtime logic changes.

## Purpose

Extends the canonical decision receipt schema (`commit_decision_<hash>.json`) with a `crypto_posture` section that captures algorithm suite, key provenance, and policy alignment for post-quantum cryptography (PQC) governance.

This extension supports deterministic, replayable receipts under DDIL/EMCON conditions and enables CI-level validation of crypto posture compliance.

## Schema: `crypto_posture` Section

The following fields are added as a top-level object within the receipt envelope:

```json
{
  "crypto_posture": {
    "alg_suite": "<string: algorithm suite identifier, e.g. ML-KEM-768, ML-DSA-65, SLH-DSA-128s, or composite>",
    "key_origin": "<string: key source — e.g. HSM, onboard_kms, ground_authority, external_ca>",
    "rotation_epoch": "<string: ISO 8601 datetime or epoch marker for key rotation lifecycle>",
    "policy_hash": "<string: SHA-256 hash of the policy document authorizing this posture>",
    "toolchain_provenance": "<string: identifier for firmware/toolchain build used>"
  }
}
```

## Field Definitions

| Field | Type | Required | Description |
|---|---|---|---|
| `alg_suite` | string | YES | NIST PQC algorithm identifier (ML-KEM, ML-DSA, SLH-DSA) or composite/hybrid identifier |
| `key_origin` | string | YES | Source of the cryptographic key material |
| `rotation_epoch` | string | YES | Key lifecycle / rotation epoch marker (ISO 8601) |
| `policy_hash` | string | YES | SHA-256 hash of the governing policy at decision time |
| `toolchain_provenance` | string | YES | Build provenance identifier for the signing/encryption toolchain |

## Validation Rules

1. All five fields MUST be present when `crypto_posture` is included in a receipt.
2. `alg_suite` MUST match an entry in the approved algorithm registry (see conformance vectors).
3. Unknown or empty `alg_suite` values MUST result in `REFUSE` (fail-closed).
4. `policy_hash` MUST be a valid SHA-256 hex string (64 characters).
5. Receipts with `crypto_posture` MUST be canonicalized per RFC 8785 (JCS) when `--canonicalization jcs` is selected.

## Integration with Existing Receipt Envelope

The `crypto_posture` section is an optional extension to the existing `commit_decision_<hash>.json` envelope. When present, it is included alongside the existing fields:

```json
{
  "verdict": "ALLOW",
  "reasons": ["allowlist_match"],
  "decision_hash": "<sha256>",
  "request_hash": "<sha256>",
  "artefact_version": "0.2",
  "schema_version": "0.2.0",
  "crypto_posture": { ... }
}
```

## Reason Codes (Crypto Posture)

The following reason codes are added to the enumerated registry for crypto-posture decisions:

| Reason Code | Verdict | Description |
|---|---|---|
| `crypto_posture_approved` | ALLOW | Posture matches approved policy |
| `crypto_posture_hybrid_approved` | ALLOW | Hybrid classic+PQC posture approved by policy |
| `crypto_posture_unknown_suite` | REFUSE | Algorithm suite not in approved registry |
| `crypto_posture_invalid_signature` | REFUSE | Signature verification failed or algorithm mismatch |
| `crypto_posture_policy_mismatch` | REFUSE | Posture does not match governing policy hash |

## Notes

- This document describes **interface-level schema only**.
- No runtime decision logic, gate evaluation, or proprietary algorithms are included.
- All contributions are independent designs; no proprietary system internals are exposed.
