# Runbook — BTC Volatility Spike Detector

## Startup (cold)

```bash
cp .env.example .env                   # one-time
docker compose up -d --build           # ~30s for Kafka healthcheck to go green
docker compose ps                      # all 8 services should be Up
curl http://localhost:8000/health      # → {"status":"ok"}
```

Open dashboards:

- API metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090 (Status → Targets should show all `up`)
- Grafana: http://localhost:3000 → dashboard "BTC Volatility Detector — API"
- MLflow: http://localhost:5001

## Smoke test

```bash
curl -X POST http://localhost:8000/predict \
     -H 'Content-Type: application/json' \
     -d @handoff/data_sample/sample.json
# → {"scores":[…],"model_variant":"ml","version":"v1.0", …}

python tests/load_test.py              # 100 burst requests, expect p95 < 800ms
```

## Rollback (ML → baseline)

When the ML variant misbehaves (latency burns budget, error spike, drift alert), fall back to the deterministic baseline:

```bash
# In .env (or one-shot):
MODEL_VARIANT=baseline docker compose up -d api
curl http://localhost:8000/version | jq .variant     # "baseline"
```

Roll forward when ready:

```bash
MODEL_VARIANT=ml docker compose up -d api
```

The Grafana **Active variant** stat panel reflects the change within ~10 s of the next Prometheus scrape.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `kafka` container restarts in a loop | Stale KRaft volume after image upgrade | `docker compose down -v` then `docker compose up -d --build` (wipes Kafka volume, OK in replay mode) |
| `ingestor` exits with `Kafka bootstrap … not reachable` | Started before `kafka-init` finished | `docker compose restart ingestor` (the service has `restart: on-failure` so it usually self-heals) |
| `featurizer` runs but `ticks.features` offset stays at 0 | First 60 s of ticks are still in the label-delay buffer | Wait — labels emit only after `horizon_sec` (60 s) of future history. Confirm with `docker exec kafka kafka-run-class kafka.tools.GetOffsetShell --broker-list kafka:29092 --topic ticks.features --time -1` |
| `/predict` returns 500 with `Model not found` | Volume mount didn't pick up `lr_pipeline.pkl` | Rebuild API: `docker compose up -d --build api` |
| Grafana panels say "No data" | Prometheus hasn't scraped yet, or `api` job is `down` | Visit http://localhost:9090/targets and check the `api` row. If `down`, restart with `docker compose restart prometheus` |
| Consumer-lag panel empty | `kafka-exporter` not up | `docker compose up -d kafka-exporter`; check logs |

## Recovery

**Full reset (loses Kafka data + Grafana dashboards state, keeps source code):**

```bash
docker compose down -v
docker compose up -d --build
```

**Restart one component:**

```bash
docker compose restart <service>       # e.g. featurizer
docker logs -f <service>
```

**Inspect Kafka topic offsets:**

```bash
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list kafka:29092 --topic ticks.raw --time -1
docker exec kafka kafka-run-class kafka.tools.GetOffsetShell \
    --broker-list kafka:29092 --topic ticks.features --time -1
```

**Regenerate drift report:**

```bash
python scripts/drift_report.py \
    --reference handoff/data_sample/features_slice.csv \
    --current   data/processed/features.parquet \
    --out       reports/drift_$(date +%Y%m%d).html
```

## Shutdown

```bash
docker compose down                    # keeps volumes (Kafka, MLflow, Grafana state)
docker compose down -v                 # nukes everything
```
