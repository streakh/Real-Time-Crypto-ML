
# BTC Volatility Spike Detector

## Quick Start

```bash
docker compose up -d --build
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d @handoff/data_sample/sample.json
```

Real time crypto ML service that streams Coinbase style ticks into Kafka, generates rolling window features, and serves predictions via a FastAPI API. The system runs end to end in replay mode with Prometheus and Grafana monitoring, and supports rollback using MODEL_VARIANT.

## Setup

### Environment

```bash
cp .env.example .env
```

### Start Services

```bash
docker compose up -d --build
```

Wait ~30 seconds for Kafka healthcheck to pass.

### Verify Service

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

### Test Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d @handoff/data_sample/sample.json
```

The system runs fully in replay mode by default, ensuring reproducibility without external dependencies.

## Data Ingestion Modes

The default `docker compose up -d` runs the replay ingestor, which loops a 10 minute Coinbase capture through Kafka at original timestamps. This ensures reproducibility without external dependencies.

To switch to live ingestion from Coinbase public WebSocket:

```bash
docker compose stop ingestor
docker compose --profile live up -d ws-ingestor
```

Both ingestion modes publish to the same `ticks.raw` Kafka topic, so only one should run at a time.


## Endpoints and Dashboards

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
curl -s http://localhost:8000/version | jq .variant   # → "baseline"
```

Roll forward with `MODEL_VARIANT=ml docker compose up -d api`. The Grafana **Active variant** panel reflects the change within ~10 s.

## Repository Structure

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

The `handoff/` folder is the original handoff bundle from the individual assignment — preserved verbatim for provenance. It contains its own `README.md`, `docker/compose.yaml`, and docs. **The canonical compose for running the system is `docker-compose.yaml` at the repo root**, not the one inside `handoff/`.

## CI

GitHub Actions runs Black + Ruff + a smoke test on every push (`.github/workflows/ci.yaml`).
