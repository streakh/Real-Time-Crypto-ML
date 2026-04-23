# Latency Report

## Test setup

- **Tool:** `tests/load_test.py` — 100 concurrent requests via `ThreadPoolExecutor` (max_workers = 100), single-row payload per request.
- **Target:** `http://localhost:8000/predict`
- **Variant:** `MODEL_VARIANT=ml` (sklearn LR pipeline)
- **Environment:** Apple M2 MacBook Pro, Docker Desktop, all 9 long-running services active (Kafka + ingestor + featurizer + predict-bridge + API + MLflow + Prometheus + Grafana + kafka-exporter).
- **Run date:** Audited live run on `2026-04-22`
- **Reproduce:**

  ```bash
  docker compose up -d
  python tests/load_test.py
  ```

## Results

| Metric | Value |
|---|---:|
| Requests sent | 100 |
| Succeeded (HTTP 200) | 100 (100 %) |
| Failed | 0 |
| Latency p50 | 400.0 ms |
| Latency p95 | **465.8 ms** |
| Latency p99 | 482.8 ms |
| Latency max | 482.8 ms |

## SLO check

p95 SLO target: **≤ 800 ms** → measured **465.8 ms** → **PASS** with ~1.7× headroom.

## Notes

- The figures above reflect the audited live run from `2026-04-22`, so they supersede the older lower numbers from earlier local measurements.
- The tighter clustering between p50 and p99 (~83 ms spread) still reflects a fairly stable ML scoring path under this burst size: a single sklearn `predict_proba` call remains the dominant operation.
- The featurizer and ingestor were actively running during the test, so this number reflects realistic contention from the streaming workload, not an idle container.
- `MODEL_VARIANT=baseline` would be slightly faster (no sklearn call), but was not retested here because the SLO targets the production `ml` variant.
