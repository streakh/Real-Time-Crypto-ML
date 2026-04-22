# BTC Volatility Spike Detector

Real-time crypto ML service: Coinbase-style ticks → Kafka → rolling-window features → FastAPI prediction. Runs end-to-end in replay mode from a bundled 10-minute sample, with Prometheus + Grafana monitoring and a `MODEL_VARIANT=ml|baseline` rollback toggle.

## Canonical startup

```bash
cp .env.example .env   # optional: override defaults
docker compose up -d
# Wait ~30s for Kafka and MLflow init, then:
curl http://localhost:8000/health
```

Use this root README together with the root `docker-compose.yaml` as the only startup guide for the team project.

## Quick Test

```bash
curl -X POST http://localhost:8000/predict \
  -H 'Content-Type: application/json' \
  -d @handoff/data_sample/sample.json
```

The `sample.json` payload contains one feature row (row 1 of `handoff/data_sample/features_slice.csv`):

```json
{
  "rows": [{
    "log_return": 0.0,
    "spread_bps": 0.0014345986913609724,
    "vol_60s": 0.0,
    "mean_return_60s": 0.0,
    "trade_intensity_60s": 0.016666666666666666,
    "n_ticks_60s": 1,
    "spread_mean_60s": 0.010000000009313226,
    "ts": "2026-04-06T15:02:34.590029Z"
  }]
}
```

Expected response (`ts` is UTC wall-clock at inference time):

```json
{
  "scores": [0.10401],
  "model_variant": "ml",
  "version": "v1.0",
  "ts": "YYYY-MM-DDTHH:MM:SS.ffffffZ"
}
```

## Replay vs live ingestion

The default `docker compose up -d` runs the **replay** ingestor — loops a 10-minute Coinbase capture through Kafka at the original timestamps. Reproducible, no network dependency, what graders should run.

To switch to **live** ingestion from Coinbase's public WebSocket (no API keys required, public ticker channel):

```bash
docker compose stop ingestor
docker compose --profile live up -d ws-ingestor
```

Both services publish to the same `ticks.raw` topic, so run only one at a time. The featurizer, API, and monitoring stack are agnostic to the source — same Kafka payload schema either way.

## Endpoints & dashboards

| Service | URL | Notes |
|---|---|---|
| API | http://localhost:8000 | `/health`, `/predict`, `/version`, `/metrics` |
| MLflow | http://localhost:5001 | Training-run tracking |
| Prometheus | http://localhost:9090 | Scrapes API + kafka-exporter |
| Grafana | http://localhost:3000 | Anonymous viewer; dashboard "BTC Volatility Detector — API" |

## Rollback

To switch from the LR model to the deterministic baseline rule:

```bash
MODEL_VARIANT=baseline docker compose up -d api
curl -s http://localhost:8000/version | jq .source   # → "pickle"
```

Roll forward with `MODEL_VARIANT=ml docker compose up -d api`. The Grafana **Active variant** panel reflects the change within ~10 s.

## Repo layout

```
api/             FastAPI prediction service (loads lr_pipeline.pkl)
features/        Featurizer Kafka consumer + rolling-window functions
scripts/         replay_to_kafka.py, ws_ingest.py, replay.py, drift_report.py
tests/           Smoke tests (test_api.py) + load test (load_test.py)
docker/          Dockerfile.api + Dockerfile.worker + requirements files
monitoring/      prometheus.yml + Grafana provisioning + dashboard JSON
docs/            Operational docs (see below)
handoff/         Original team handoff bundle (model, data, reports, rationale)
docker-compose.yaml   Canonical 8-service stack
config.yaml           Featurizer config
```

## Documentation

| Doc | Purpose |
|---|---|
| [`docs/results.md`](docs/results.md) | Single-page scorecard: latency, success rate, PR-AUC vs baseline, rollback proof |
| [`docs/slo.md`](docs/slo.md) | Service Level Objectives + error budgets |
| [`docs/latency_report.md`](docs/latency_report.md) | Load-test methodology and percentiles |
| [`docs/drift_summary.md`](docs/drift_summary.md) | Evidently train-vs-test drift findings |
| [`docs/runbook.md`](docs/runbook.md) | Cold start, smoke test, rollback, common failures, recovery |
| [`handoff/SELECTED_BASE_NOTE.md`](handoff/SELECTED_BASE_NOTE.md) | Model selection rationale (ablation study) |
| [`handoff/docs/`](handoff/docs/) | Architecture diagram, feature spec, model card, team charter |

## Notes on `handoff/`

The `handoff/` folder preserves the original Part 1 handoff artifacts for reference and compliance. It is not the runtime entrypoint for the Part 2 team project. Do not launch the system from `handoff/README.md` or `handoff/docker/compose.yaml`; use this root README and the root `docker-compose.yaml` instead.

## CI

GitHub Actions runs Black + Ruff + a smoke test on every push (`.github/workflows/ci.yaml`).
