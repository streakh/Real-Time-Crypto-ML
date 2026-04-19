# BTC Volatility Spike Detector

Real-time crypto ML service: Coinbase-style ticks → Kafka → rolling-window features → FastAPI prediction. Runs end-to-end in replay mode from a bundled 10-minute sample, with Prometheus + Grafana monitoring and a `MODEL_VARIANT=ml|baseline` rollback toggle.

## Run

```bash
cp .env.example .env
docker compose up -d --build
# Wait ~30s for Kafka healthcheck, then:
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
     -H 'Content-Type: application/json' \
     -d @handoff/data_sample/sample.json
```

URLs: API `:8000` (`/health`, `/predict`, `/version`, `/metrics`) · MLflow `:5001` · Prometheus `:9090` · Grafana `:3000` (anonymous viewer; dashboard "BTC Volatility Detector — API"). To roll back to the baseline rule, set `MODEL_VARIANT=baseline` in `.env` and run `docker compose up -d api`. See `handoff/docs/` for architecture, feature spec, model card, and selection rationale.
