# Service Level Objectives — BTC Volatility Spike Detector

These SLOs cover the public-facing prediction API (`api` service) and the streaming pipeline that feeds it. They are aspirational targets, not pass/fail thresholds — their purpose is to make degradation observable in Grafana and give on-call a clear "something is wrong" signal.

## SLOs

| # | Objective | Target | Measurement window | Source metric (PromQL) |
|---|---|---|---|---|
| 1 | **Prediction latency p95** | ≤ 800 ms | rolling 5 min | `histogram_quantile(0.95, sum by (le) (rate(predict_latency_seconds_bucket[5m])))` |
| 2 | **Prediction latency p50** | ≤ 100 ms | rolling 5 min | `histogram_quantile(0.50, sum by (le) (rate(predict_latency_seconds_bucket[5m])))` |
| 3 | **Request success rate** | ≥ 99 % | rolling 5 min | `1 - (sum(rate(predict_errors_total[5m])) / clamp_min(sum(rate(predict_requests_total[5m])), 0.001))` |
| 4 | **Replay lag: raw -> featurizer** | ≤ 200 messages on `ticks.raw` | rolling 1 min | `sum(kafka_consumergroup_lag{topic="ticks.raw", consumergroup="ticks-featurizer"})` |
| 5 | **Replay lag: features -> predict** | ≤ 200 messages on `ticks.features` | rolling 1 min | `sum(kafka_consumergroup_lag{topic="ticks.features", consumergroup="predict-bridge"})` |
| 6 | **Prediction freshness at API** | ≤ 120 s | continuous | `feature_freshness_seconds` |
| 7 | **Service availability (`/health`)** | ≥ 99.5 % | 24 h | Compose healthcheck on `api` |

## Error budget

- **Latency budget:** 5 % of requests / month may exceed 800 ms.
- **Error budget:** 1 % of requests / month may return 5xx.
- **Freshness budget:** either replay hop may exceed 200 queued messages for at most 30 min / day, and `feature_freshness_seconds` may exceed 120 s only during active incident response.

If any budget is burned more than 50 % within a 24 h window, the on-call action is to **toggle `MODEL_VARIANT=baseline`** (see [runbook.md](runbook.md)) and investigate before re-enabling the ML variant.

## Current measured baseline

100-request burst load test, single-row payload, API running locally on M2 MacBook against the in-loop replay pipeline:

| Metric | Value | vs SLO |
|---|---:|:---:|
| p50 latency | 236.8 ms | within target |
| p95 latency | 255.2 ms | within target (target 800 ms) |
| p99 latency | 256.9 ms | n/a |
| Success rate | 100 % | within target |

Full report: [latency_report.md](latency_report.md).

## Out of scope

- Cold-start latency (model load takes ~2 s; not measured here).
- WebSocket ingestor uptime — the shipped build runs in replay mode by default, with the live WebSocket ingestor available only under the optional `live` profile.
- MLflow tracking server availability — non-critical (model is loaded from the on-disk artifact, not from MLflow).
