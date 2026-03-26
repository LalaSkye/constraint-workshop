# ADMISSIBILITY_ALGEBRA_v1

**Artifact ID:** `ADMISSIBILITY_ALGEBRA_v1`
**Status:** FROZEN_DRAFT
**Mode:** NON_EXEC / FORMAL_SPEC
**Scope:** Foundation layer for execution-boundary governance
**Author:** Ricky Jones (LalaSkye)
**Date:** 2026-03-26

---

## 0. Purpose

Define the minimal formal algebra over which all admissibility decisions are computed.

Every verdict, every proof obligation, every conformance check, and every contradiction classification depends on this algebra being exact.

If this layer is loose, everything above it is decorative.

---

## 1. Primitives

The algebra operates over exactly eight primitives:

| Primitive | Type | Description |
|-----------|------|-------------|
| `Actor` | string | The identity requesting execution |
| `Action` | enum | A member of the registered action set |
| `Object` | string | The target of the requested action |
| `State` | hash | The current system state at evaluation time |
| `Authority` | enum | `{valid, invalid, unknown}` |
| `Time` | ISO 8601 | The timestamp at which authority is evaluated |
| `Dependency` | list | Preconditions that must be satisfied |
| `Verdict` | enum | `{ALLOW, DENY, HOLD, ESCALATE}` |

No primitive may be omitted from evaluation.
No primitive may be inferred from another.

---

## 2. Verdict Algebra

### 2.1 Verdict Set

```
V = {ALLOW, DENY, HOLD, ESCALATE}
```

### 2.2 Execution Predicate

```
execute(action) iff verdict(action) == ALLOW
```

No other verdict permits execution.
No derived execution.
No implied authority.
No inherited commit rights.

### 2.3 Verdict Precedence

```
DENY > HOLD > ESCALATE > ALLOW
```

If any evaluation path yields DENY, the final verdict is DENY regardless of other paths.

### 2.4 Default Verdict

If no rule explicitly produces a verdict:

```
default_verdict = DENY
```

The system is fail-closed.

---

## 3. Authority Function

```
authority := f(actor, action, object, state, time, dependencies)
```

### 3.1 Freshness Invariant

Authority must be recomputed at the exact point of state mutation.

Never permit:
- Cached approval reuse
- Inherited approval
- "It was allowed one step earlier"
- Conversational authority drift

### 3.2 Time Is Load-Bearing

The `time` parameter is not metadata. It is a first-class input to the authority function. A valid authority at `t` is not valid at `t+1` unless recomputed.

---

## 4. Action Registry

```
ACTION in REGISTERED_ACTIONS
```

All actions must be members of a finite, explicit, closed registry.

If `action not in REGISTERED_ACTIONS`:

```
verdict = DENY
reason_code = unknown_action
```

No free-language execution fields at commit boundary.
No creative interpretation.

---

## 5. State Transition Rules

### 5.1 Admissible Transition

A state transition `S -> S'` is admissible iff:

1. The requesting `Actor` is bound
2. The `Action` is registered
3. The `Object` exists
4. `Authority` evaluates to `valid` at current `Time`
5. All `Dependencies` are satisfied
6. The `Policy` permits the action
7. No contradiction is detected

All seven conditions must hold simultaneously.
Partial satisfaction = DENY.

### 5.2 Forbidden Transitions

The following transitions are unconditionally forbidden:

| From | To | Reason |
|------|----|--------|
| Any state | Execution | Authority absent |
| Any state | Execution | Actor unbound |
| Any state | Execution | Action unregistered |
| Any state | Execution | Dependency unresolved |
| Any state | Execution | State hash mismatch |
| Any state | Execution | Replay detected |

Forbidden transitions cannot be overridden by policy.

---

## 6. Contradiction Classes

A contradiction exists when a request requires mutually inconsistent conditions.

| Class | Condition |
|-------|-----------|
| `AUTHORITY_CONTRADICTION` | No valid authority + commit requested |
| `OBJECT_CONTRADICTION` | Object absent + modify requested |
| `ACTOR_CONTRADICTION` | Actor unbound + privileged action |
| `STATE_CONTRADICTION` | State hash mismatch + transition requested |
| `DEPENDENCY_CONTRADICTION` | Dependency unresolved + execution demanded |
| `TEMPORAL_CONTRADICTION` | Authority expired + execution requested |

All contradictions route to the Paradox Vector (non-mutating contradiction sink).

No contradiction path may produce execution.

---

## 7. Reason Code Registry

Every verdict must include exactly one reason code.

| Reason Code | Verdict | Meaning |
|-------------|---------|--------|
| `policy_allow_with_valid_authority` | ALLOW | All conditions met |
| `policy_violation` | DENY | Policy forbids action |
| `authority_ambiguous` | ESCALATE | Authority cannot be determined |
| `unknown_action` | DENY | Action not in registry |
| `malformed_input` | DENY | Structural validation failed |
| `replay_detected` | DENY | Request ID already processed |
| `default_deny` | DENY | No explicit rule matched |
| `contradiction_detected` | DENY | Paradox vector triggered |

---

## 8. Decision Record

Every verdict produces a decision record containing:

```
{
  request_id:   string,
  scenario:     string,
  decision:     Verdict,
  reason_code:  string,
  executed:     boolean,
  timestamp:    ISO 8601,
  state_hash:   string,
  prior_hash:   string
}
```

Decision records are hash-chained. No silent modification.

---

## 9. Non-Goals

This algebra does NOT:
- Define implementation language or runtime
- Specify network transport or API shape
- Provide policy authoring tools
- Include AI model evaluation
- Offer probabilistic or heuristic verdicts
- Support "soft" denials or advisory modes

---

## 10. Invariants

1. `execute(action) iff verdict(action) == ALLOW` — no exceptions
2. `default_verdict == DENY` — fail-closed
3. `authority` is recomputed per-decision — never cached
4. `action in REGISTERED_ACTIONS` — closed world
5. All contradictions sink to non-execution — no contradiction produces state mutation
6. Same input produces same verdict — deterministic
7. Decision records are hash-chained — tamper-evident
8. No primitive may be omitted — completeness required

---

## 11. Test Requirements

Any implementation claiming conformance must pass:

- All registered actions produce correct verdicts
- All unregistered actions produce DENY
- Replay of any request_id produces DENY
- Malformed input produces DENY
- Authority=unknown produces ESCALATE
- Authority=invalid produces DENY
- All contradiction classes route to sink
- Default path produces DENY
- Decision log is hash-chained and verifiable
- Same input always produces same output

---

## 12. Conformance

Two implementations are equivalent iff they produce identical verdicts and identical reason codes for every packet in the canonical conformance corpus.

Different verdicts for the same input = not equivalent.
Different reason codes for the same input = not equivalent.

---

*This artefact is the foundation layer. All subsequent specs (PROOF_CARRYING_PACKET_SPEC_v1, CANONICAL_PACKET_NORMAL_FORM_v1, GOLDEN_CONFORMANCE_CORPUS_v1) depend on this algebra being exact.*
