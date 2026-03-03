# LV/TECH — RUNTIME GOVERNANCE GEOMETRY: DIAGRAM v0.1

Canonical Mermaid diagram for the runtime governance geometry.

GitHub renders this automatically in markdown preview.

## Flow direction

- **Top to Bottom** = increasing containment
- **Left to Right** = increasing irreversibility
- Only **G4 PASS** crosses the COMMIT_BOUNDARY

## Diagram

```mermaid
flowchart TD
    A["A: UNCONTROLLED"]
    B["B: GOVERNED_PENDING"]
    C["C: COMMITTED"]
    D["D: QUARANTINED"]
    E["E: REJECTED"]
    CB{{"COMMIT_BOUNDARY"}}

    A -->|"G1 PASS"| B
    A -->|"G1 FAIL"| E

    B -->|"G2 FAIL"| E
    B -->|"G2 FAIL (severe)"| D
    B -->|"G3 FAIL"| D
    B -->|"G3 FAIL"| E

    B -->|"G4 PASS"| CB
    CB --> C

    B -->|"G4 FAIL"| B
    B -->|"G4 FAIL"| E

    style CB fill:#ff6600,stroke:#ff3300,stroke-width:4px,color:#fff
    style C fill:#006600,stroke:#004400,stroke-width:2px,color:#fff
    style D fill:#cc6600,stroke:#993300,stroke-width:2px,color:#fff
    style E fill:#660000,stroke:#440000,stroke-width:2px,color:#fff
    style A fill:#333,stroke:#555,stroke-width:2px,color:#fff
    style B fill:#003366,stroke:#002244,stroke-width:2px,color:#fff
```

## Legend

| Symbol | Meaning |
|--------|---------|
| **A** | Uncontrolled: pre-governance, no binding |
| **B** | Governed/Pending: evaluated, not committed |
| **C** | Committed: system-of-record changed |
| **D** | Quarantined: blocked/held for investigation |
| **E** | Rejected: dropped, no side-effects |
| **CB** | COMMIT_BOUNDARY: crossed only via G4 PASS; one-way |
| G1–G4 | Deterministic gates with PASS/FAIL outcomes |
| Solid arrow | Deterministic transition |

## Invariants (visual check)

- [ ] No arrow reaches C except through CB (G4 PASS)
- [ ] All FAIL arrows point to D or E
- [ ] CB is visually distinct (orange/heavy)
- [ ] No arrow from D or E leads to C

---

**END DIAGRAM — v0.1**
