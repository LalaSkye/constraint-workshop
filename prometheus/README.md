# Prometheus Anomaly Surveyor v0.1

> Observability island. Read-only. Deterministic. No authority.

## What this is

Prometheus is a **read-only anomaly surveyor** that lives under `/prometheus/*`
inside `constraint-workshop`. It ingests diagnostic event streams (JSONL),
aggregates anomaly statistics, scans its own code for governance red-line
violations, and produces a deterministic fit report.

It has **no execution authority**. It cannot allow, hold, deny, or silence
anything. It observes and reports.

## Scope

- **NON_EXEC** — no schedulers, runners, deploy hooks, or automation.
- **Observability only** — reporting, aggregation, red-line scanning.
- **Island** — never imported by `/trinity/gate/` or `/alviantech/pipeline/`.
- **Contained** — writes only under `/prometheus/*`.

## Inputs

- DiagEvent JSONL files under `prometheus/fixtures/*.jsonl` (test mode)
- DiagEvent JSONL files under `prometheus/diag/*.jsonl` (runtime mode)

## Outputs (deterministic, JSON, sorted keys)

| Output | Path |
|---|---|
| Anomaly Summary | `prometheus/agg/anomaly_summary.json` |
| Fit Report | `prometheus/reports/prometheus_fit_report.json` |
| Red-line Findings | `prometheus/lint/prometheus_redlines.json` |

## Determinism guarantee

Same inputs + same repo snapshot => byte-identical outputs.
All JSON uses `sort_keys=True, indent=2`. File ordering is lexicographic.

## Verdicts

| Verdict | Condition |
|---|---|
| `FIT_CLEAN` | No schema errors, no red-line findings, no forbidden content in invalid events |
| `FIT_WITH_WARNINGS` | Schema-invalid events exist, but no forbidden content and no red-lines |
| `DRIFT_RISK` | Red-line finding in code OR forbidden content found in invalid event data |

## Red-line rules

- **Forbidden paths**: `/trinity/gate/`, `/alviantech/pipeline/`
- **Forbidden tokens**: case-insensitive match
- **Scanner scope**: `src/**/*.py` only (never scans README, fixtures, expected)

## Run

```bash
cd constraint-workshop
python -m pytest prometheus/tests/ -q
```

## Version

`prometheus_anomaly_surveyor_v0.1`

## License

Same as parent repo (Apache-2.0).
