# Demo Script — 8-minute walkthrough

## Pre-record (off camera)

```bash
docker compose down -v
cp .env.example .env
docker compose build
```

Open three terminal panes:

- **Left** — compose / docker commands
- **Top-right** — `curl` and `jq`
- **Bottom-right** — `docker logs` follows

And four browser tabs:

1. http://localhost:8000/metrics
2. http://localhost:9090/targets (Prometheus)
3. http://localhost:3000 → "BTC Volatility Detector — API" (Grafana)
4. http://localhost:5001 (MLflow)

---

## 0:00 – 0:45 — Frame the problem + cold start

> "This is a real-time BTC volatility-spike detector. Coinbase ticks come in over Kafka, get featurized in 60-second rolling windows, and a logistic-regression model serves predictions over HTTP. Today I'll show the full stack come up cold, run on **both replay and live Coinbase data**, hit the SLOs, and survive a rollback."

```bash
docker compose up -d
docker compose ps
```

Point to all 8 services `Up` / `(healthy)`.

---

## 0:45 – 1:30 — Smoke test the API

```bash
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/version | jq .
curl -s -X POST http://localhost:8000/predict \
     -H 'Content-Type: application/json' \
     -d @handoff/data_sample/sample.json | jq .
```

Call out in `/version`: `model_path`, `git_sha`, `variant: "ml"`, `baseline_vol_threshold`. Then:

```bash
curl -s http://localhost:8000/metrics | grep predict_request
```

> "Prometheus counters already accumulating, labeled by `model_variant` so the rollback toggle is observable end-to-end."

---

## 1:30 – 2:30 — Replay pipeline is actually streaming

```bash
docker logs --tail 5 ingestor
docker logs --tail 5 featurizer
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list kafka:29092 --topic ticks.raw --time -1
sleep 8
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list kafka:29092 --topic ticks.raw --time -1
```

> "Default mode is **replay** — looping a 10-minute Coinbase capture through Kafka at the original timestamps. Reproducible for grading. Offsets clearly growing between the two reads."

---

## 2:30 – 3:30 — Swap to live Coinbase ingestion

> "But the brief asks for live data from Coinbase. Replay is the default; live is one command away."

```bash
docker compose stop ingestor
docker compose --profile live up -d ws-ingestor
docker logs -f ws-ingestor
```

Wait for: `[ticker] subscribed for BTC-USD → topic 'ticks.raw'`. `Ctrl-C` the follow.

```bash
docker exec kafka kafka-console-consumer \
    --bootstrap-server kafka:29092 --topic ticks.raw \
    --max-messages 1 --timeout-ms 5000
```

> "Real BTC tick from Coinbase, sub-second timestamp, same payload schema as replay. The featurizer and API didn't restart — Kafka decouples the source from everything downstream."

Switch back so the demo stays reproducible:

```bash
docker compose stop ws-ingestor
docker compose up -d ingestor
```

---

## 3:30 – 4:45 — Observability tour + load test

Switch to the Grafana tab. Walk the panels left-to-right:

1. **Active variant** — `ml` highlighted.
2. **p95 latency** — well under the 800 ms SLO line.
3. **p50 latency** — for context.
4. **Request rate by variant**.
5. **Error rate by variant** — flat at zero.
6. **Kafka consumer lag** — featurizer's group, small and stable.

Then trigger a spike on camera:

```bash
python tests/load_test.py
```

Read result aloud: 100/100 success, p95 ~66 ms. Tie back to [`latency_report.md`](./latency_report.md) and [`slo.md`](./slo.md) — ~12× headroom on the latency SLO.

---

## 4:45 – 6:00 — Rollback drill (ML → baseline → ML)

> "If the ML model misbehaves — drift, latency burn, error spike — we fall back to the deterministic baseline rule with one environment variable. Same code path is used as the science baseline, so the rollback target is the documented baseline, not a degraded approximation."

```bash
MODEL_VARIANT=baseline docker compose up -d api
sleep 3
curl -s http://localhost:8000/version | jq '.variant, .baseline_vol_threshold'
curl -s -X POST http://localhost:8000/predict \
     -H 'Content-Type: application/json' \
     -d @handoff/data_sample/sample.json | jq '.model_variant, .scores'
python tests/load_test.py
```

Show: `variant` flipped to `"baseline"`, scores are now hard 0/1 from the threshold rule. Switch to Grafana — Active variant panel flips, request-rate splits to the `baseline` series.

```bash
MODEL_VARIANT=ml docker compose up -d api
sleep 3
curl -s http://localhost:8000/version | jq '.variant'
python tests/load_test.py
```

> "Three load-test spikes are now visible on the Grafana dashboard — one ml, one baseline, one ml — proving the rollback round-trips cleanly."

---

## 6:00 – 7:00 — Failure recovery

```bash
docker compose stop ingestor
```

Switch to Grafana. Within ~30 s the Kafka consumer-lag panel plateaus (no new raw ticks). API stays healthy on the Prometheus targets page.

```bash
docker compose start ingestor
```

Watch lag drain back down. Mention the runbook covers Kafka volume corruption, missing model artifact, and Grafana "No data" with the same one-line-fix pattern.

---

## 7:00 – 8:00 — Wrap-up + provenance

```bash
ls docs/
```

Call out, briefly:

- [`docs/results.md`](./results.md) — single-page scorecard + Grafana screenshot of the run you just watched.
- [`docs/slo.md`](./slo.md), [`latency_report.md`](./latency_report.md), [`drift_summary.md`](./drift_summary.md), [`runbook.md`](./runbook.md) — operational docs.
- [`handoff/SELECTED_BASE_NOTE.md`](../handoff/SELECTED_BASE_NOTE.md) — model selection rationale (ablation study, Variant B winner).
- MLflow tab — every training run logged with params, metrics, and the artifact mounted into the API container.
- CI: GitHub Actions runs Black + Ruff + smoke test on every push.

Closing line:

> "End-to-end real-time inference, runs on both replay and live Coinbase data, 100 % success at p95 ≈ 66 ms, model beats the rule-based baseline by ~9 % PR-AUC, and rollback is one env var with sub-10-second propagation. That's the deliverable."

---

## Recording tips

- **Pre-build** with `docker compose build` before recording so the cold-start beat is `up -d`, not `up --build`.
- The two slow beats are the Kafka offset wait (1:30) and the live-ingest connection (2:30 — usually < 5 s but Coinbase sometimes takes ~15 s). During those waits, narrate the architecture instead of waiting silently.
- **If you overrun**, the easiest cut is the failure-recovery beat (6:00 – 7:00) — it's already in the runbook. Live ingestion (2:30 – 3:30) is the second-easiest cut but it's the strongest single beat in the demo, so keep it if at all possible.
- **Camera order trick:** record the live-ingestion beat first while you have a fresh Coinbase connection, then go back and record the cold-start beat. Your editor will reorder them; viewers won't know.
