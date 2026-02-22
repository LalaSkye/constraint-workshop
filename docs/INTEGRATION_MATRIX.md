# Integration Matrix

## Canonical Primitives

| Primitive | Canonical Repo | File | Pinned Commit |
|-----------|---------------|------|---------------|
| `stop_machine` | constraint-workshop | `stop_machine.py` | `3780882` |
| `authority_gate` | constraint-workshop | `authority_gate.py` | `70ed2c9` |
| `invariant_litmus` | constraint-workshop | `invariant_litmus.py` | `8d04cbc` |

## Downstream Repos

| Repo | Status | v0 Stubs | Drift Alarms | CI |
|------|--------|----------|--------------|----|
| [stop-machine](https://github.com/LalaSkye/stop-machine) | v0 folders stubbed (disabled) | `primitives/stop-machine-v0/`, `primitives/authority-gate-v0/` | Active (grep-based) | [CI](https://github.com/LalaSkye/stop-machine/actions) |

## Evidence Links

- **constraint-workshop CI**: https://github.com/LalaSkye/constraint-workshop/actions
- **stop-machine CI**: https://github.com/LalaSkye/stop-machine/actions
- **stop-machine CANONICAL.md**: https://github.com/LalaSkye/stop-machine/blob/main/CANONICAL.md
- **stop-machine PR #2 (stubbing)**: https://github.com/LalaSkye/stop-machine/pull/2

## Rules

1. Canonical source lives in `constraint-workshop`.
2. Downstream repos contain stubs only.
3. Update canonical first, then resync downstream.
4. CI drift alarms prevent re-introduction of v0 implementations.
