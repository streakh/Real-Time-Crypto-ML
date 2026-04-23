# Latency Report

This report summarizes the latency performance of the prediction API under burst load conditions.

## Test setup

- **Tool:** `tests/load_test.py` — 100 concurrent requests via `ThreadPoolExecutor` (max_workers = 100), single-row payload per request.
- **Target:** `http://localhost:8000/predict`
- **Variant:** `MODEL_VARIANT=ml` (sklearn LR pipeline)
- **Environment:** Apple M2 MacBook Pro, Docker Desktop, all 8 services running concurrently (Kafka + ingestor + featurizer + API + MLflow + Prometheus + Grafana + kafka-exporter).
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
| Latency p50 | 56.9 ms |
| Latency p95 | **66.1 ms** |
| Latency p99 | 68.7 ms |
| Latency max | 68.7 ms |

## SLO Check

p95 SLO target: **≤ 800 ms** → measured **66.1 ms** → **PASS** with ~12× headroom.

## Observations

- The tight clustering between p50 and p99 (~12 ms spread) reflects that the ML scoring path is essentially constant-time at this batch size: a single sklearn `predict_proba` call dominates.
- The featurizer and ingestor were actively running during the test, so this number reflects realistic contention from the streaming workload, not an idle container.
- The baseline variant would likely be slightly faster due to the absence of sklearn inference, but was not evaluated as the SLO applies to the production ML variant.
