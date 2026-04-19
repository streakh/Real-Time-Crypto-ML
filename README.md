# BTC Volatility Spike Detector

Real-time crypto ML service: Coinbase-style ticks → Kafka → rolling-window features → FastAPI prediction. Runs end-to-end in replay mode from a bundled 10-minute sample.

## Run

```bash
cp .env.example .env
docker compose up -d --build
# Wait ~30s for Kafka healthcheck to go green, then:
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
     -H 'Content-Type: application/json' \
     -d @handoff/data_sample/sample.json
```

Services: Kafka `:9092`, MLflow `:5001`, API `:8000` (`/health`, `/predict`, `/version`, `/metrics`). Ingestor and featurizer run headless and stream through Kafka topics `ticks.raw` → `ticks.features`. See `handoff/docs/` for architecture diagram, feature spec, model card, team charter, and selection rationale.
