# MGTP Programme Positioning (v0.1)

## Core invariant
Governance must bind at runtime, not at policy.

## Scope boundary
MGTP governs execution transitions only: tool calls, service hops, state mutations, and irreversible commits.
MGTP does not attempt global semantic safety.

## Non-goals
- No alignment claims
- No general AI safety claims
- No marketing language
- No behavioural modelling

## Lanes

### Lane A — Builds (Executable proof)
- Transition registry
- Deterministic evaluate_transition
- DecisionRecord artefacts
- Execution-boundary conformance tests

### Lane B — Articles (Translation layer)
- Runtime vs policy enforcement
- Halt rights vs monitoring
- Authority leakage at transitions

### Lane C — Academic papers (Formal model)
- State space definition
- Authority lattice
- Boundary completeness theorem sketch
- Mapping to EU AI Act Articles 9, 12, 14

## Calibre standard (acceptance criteria)
1. Deterministic (byte-identical replay)
2. No primitive mutation without explicit version bump
3. Registry version tied to ENGINEERING_STATUS.yaml
4. Transitions enumerated
5. Refusal propagation test present
6. No hidden state
7. CI matrix proof across Python versions
