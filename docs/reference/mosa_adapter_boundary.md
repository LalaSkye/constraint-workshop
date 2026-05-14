# MOSA Adapter Boundary Note

**Version:** 0.1  
**Status:** DRAFT  
**Normativity:** INFORMATIVE  
**Scope:** Interface-only boundary description — no implementation details.

## Purpose

This document describes the integration points where the Autonomy Governance & Control Kit interfaces with GFI (Government Furnished Information) ICD/API patterns via MOSA (Modular Open Systems Approach) adapters. It covers inputs, outputs, and the position of the admissibility gate in the call chain.

No implementation details, internal algorithms, or proprietary wiring are included.

## Architecture Position

The governance kit operates as a **wrapper/augmenter** around existing autonomy stacks. It does not replace platform autonomy software but interposes at defined boundary points to enforce admissibility decisions before high-impact actions execute.

```
[Platform Autonomy Stack]
        |
        v
[MOSA Adapter Interface]
        |
        v
[Admissibility Gate]  <-- fail-closed: ALLOW / REFUSE
        |
        v
[Receipt Emitter]  --> audit log + crypto posture receipt
        |
        v
[Platform Execution / Command Bus]
```

## Inputs (from GFI ICD/API patterns)

The adapter receives the following from upstream platform systems:

| Input | Description |
|---|---|
| Command intents | Structured action requests from mission planning or operator consoles |
| Mission plans | Waypoints, objectives, rules of engagement references |
| Crypto configuration | Algorithm suite selections, key rotation schedules |
| Key/rotation metadata | Key origin, lifecycle epoch, HSM/KMS identifiers |
| Policy hashes | SHA-256 hashes of governing policy documents at decision time |
| Authority chain | Delegation chain from ground authority through operational levels |

## Outputs (from the governance kit)

The adapter produces the following at its boundary:

| Output | Description |
|---|---|
| Admissibility decision | `ALLOW`, `REFUSE`, or `ESCALATE` with deterministic verdict |
| Reason codes | Single primary enumerated reason code per decision (no free-text) |
| Decision receipt | `commit_decision_<hash>.json` — canonical, replayable CI artifact |
| Crypto posture receipt | Optional `crypto_posture` section within receipt (see PQC schema) |
| Authority graph | `authority_graph_<hash>.json` — supporting evidence (not primary) |
| Audit log entries | Structured log records for platform-level audit trail integration |

## Integration Points

### 1. Admissibility Gate Position

The gate sits **between** the platform command pipeline and execution. All high-impact actions pass through the gate before reaching the command bus. The gate is fail-closed: if evaluation cannot complete or encounters unknown inputs, the default verdict is `REFUSE`.

### 2. Receipt Emission Point

Receipts are emitted **after** each admissibility decision. They are written to the local audit store and can be forwarded to platform logging infrastructure. Receipt format follows the canonical decision schema (RFC 8785 JCS when canonicalization is selected).

### 3. Mapping to Platform Logs

Receipt `decision_hash` and `request_hash` fields provide deterministic identifiers that platform logging systems can cross-reference. The adapter does not modify platform log formats — it emits its own receipts alongside existing log streams.

### 4. Delegation and Revocation Interface

The adapter accepts delegation/revocation signals from the authority chain. These modify the active authority scope for subsequent decisions. Revocation is immediate and auditable.

## Constraints

- This document describes **boundary-level interfaces only**
- No internal algorithms, proprietary protocols, or configuration grammars are included
- The adapter is platform-agnostic and hull-vendor independent
- All integration points are described at the input/output level
- No specific GFI ICD version is assumed — adapter pattern is generic
- This adapter defines interface structures only and does not implement policy evaluation or decision logic
