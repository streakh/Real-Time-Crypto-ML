# Service Level Objectives for BTC Volatility Spike Detector

These SLOs cover the public facing prediction API (`api` service) and the streaming pipeline that feeds it. They are aspirational targets, not strict pass or fail thresholds. Their purpose is to make degradation visible in Grafana and give the on call team a clear signal when intervention is needed.

## SLOs

| # | Objective | Target | Measurement window | Source metric (PromQL) |
|---|---|---|---|---|
| 1 | **Prediction latency p95** | ≤ 800 ms | rolling 5 min | `histogram_quantile(0.95, sum by (le) (rate(predict_latency_seconds_bucket[5m])))` |
| 2 | **Prediction latency p50** | ≤ 100 ms | rolling 5 min | `histogram_quantile(0.50, sum by (le) (rate(predict_latency_seconds_bucket[5m])))` |
| 3 | **Request success rate** | ≥ 99 % | rolling 5 min | `1 - (sum(rate(predict_errors_total[5m])) / clamp_min(sum(rate(predict_requests_total[5m])), 0.001))` |
| 4 | **Feature freshness (consumer lag)** | ≤ 200 ticks on `ticks.raw` | rolling 1 min | `sum(kafka_consumergroup_lag{topic="ticks.raw"})` |
| 5 | **Service availability (`/health`)** | ≥ 99.5 % | 24 h | Compose healthcheck on `api` |

## Error Budget

- **Latency budget:** 5 % of requests / month may exceed 800 ms.
- **Error budget:** 1 % of requests / month may return 5xx.
- **Freshness budget:** consumer lag may exceed 200 ticks for at most 30 min / day.

If any budget is consumed by more than 50% within a 24 hour window, the on call response is to switch `MODEL_VARIANT=baseline` as described in `runbook.md` and investigate before re enabling the ML variant..

## Current Measured Baseline

100-request burst load test, single-row payload, API running locally on M2 MacBook against the in-loop replay pipeline:

| Metric | Value | vs SLO |
|---|---:|:---:|
| p50 latency | 56.9 ms | within target |
| p95 latency | 66.1 ms | well within target (target 800 ms) |
| p99 latency | 68.7 ms | n/a |
| Success rate | 100 % | within target |

Full report: [latency_report.md](latency_report.md).

## Out of scope

- Cold-start latency (model load takes ~2 s; not measured here).
- WebSocket ingestor uptime — the shipped build runs in replay mode.
- MLflow tracking server availability — non-critical (model is loaded from the on-disk artifact, not from MLflow).
