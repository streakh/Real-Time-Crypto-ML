# Follow-ups and Deferred Work

Items tracked here are confirmed gaps or improvements deferred from the current implementation. Each entry has a status and the rationale for deferral.

## Open

| # | Item | Rationale for deferral | Priority |
|---|------|------------------------|----------|
| 1 | **Automated drift alerting** | Drift is monitored via Evidently HTML reports and the `drift_summary.md` summary, but no Prometheus alert rule or scheduled job triggers on a threshold breach. The infrastructure (Prometheus, Grafana, drift threshold = JS ≥ 0.15 in `model_card_v1.md`) is in place; wiring the alert is a one-sprint task. Deferred because the coursework deadline did not require automated alerting, only drift measurement. | Medium |
| 2 | **Long-horizon uptime measurement** | Availability is defined as an SLO (≥ 99 % success rate on `/health`) with a recovery contract in `runbook.md`, but no continuous external prober measures it over time. Deferred: the stack is a coursework deployment, not a 24×7 service. An uptime check could be wired to `/health` in the future without any API changes. | Low |
| 3 | **Scheduled drift re-run against live features** | `scripts/drift_report.py` can regenerate the Evidently report against fresh `data/processed/features.parquet`, but this is not scheduled. The current report covers the fixed train-vs-test slice. | Low |

## Closed

| # | Item | Resolution |
|---|------|------------|
| — | *(none yet)* | — |
