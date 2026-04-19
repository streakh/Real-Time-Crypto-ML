# BTC Volatility Spike Detector

Real-time crypto ML service: Coinbase-style ticks → Kafka → rolling-window features → FastAPI prediction. Runs end-to-end in replay mode from a bundled 10-minute sample, with Prometheus + Grafana monitoring and a `MODEL_VARIANT=ml|baseline` rollback toggle.

## Setup

```bash
cp .env.example .env
docker compose up -d --build
# Wait ~30s for Kafka healthcheck, then:
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
     -H 'Content-Type: application/json' \
     -d @handoff/data_sample/sample.json
```

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
curl -s http://localhost:8000/version | jq .variant   # → "baseline"
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

The `handoff/` folder is the original handoff bundle from the individual assignment — preserved verbatim for provenance. It contains its own `README.md`, `docker/compose.yaml`, and docs. **The canonical compose for running the system is `docker-compose.yaml` at the repo root**, not the one inside `handoff/`.

## CI

GitHub Actions runs Black + Ruff + a smoke test on every push (`.github/workflows/ci.yaml`).
