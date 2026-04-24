# Selection Rationale

## Problem Overview
Cryptocurrency markets are highly volatile and can experience sudden spikes in price movements. Detecting volatility spikes in real time is important for risk management, trading strategies, and monitoring market stability.

## Why This Problem
We selected this problem because it combines real time data processing with machine learning based prediction, which aligns well with the objectives of building operational AI systems. It also reflects real world use cases in financial analytics and trading systems.

## Delivered System
The final team project is an end-to-end real-time stack:

- Coinbase BTC-USD ticks enter through Kafka, either from the replay ingestor or the live WebSocket ingestor.
- The featurizer computes rolling 60-second engineered features and publishes feature rows downstream.
- The FastAPI service exposes `/health`, `/predict`, `/version`, and `/metrics`.
- MLflow tracks model versions, and Prometheus plus Grafana provide operational visibility.
- `MODEL_VARIANT=ml|baseline` gives us a documented rollback path.

## Model and API Choice
We standardized on a Logistic Regression pipeline trained on the canonical 7-feature set:
`log_return`, `spread_bps`, `vol_60s`, `mean_return_60s`,
`trade_intensity_60s`, `n_ticks_60s`, and `spread_mean_60s`.

The model ships under the MLflow registry name `btc-volatility-lr` at version `v1.0` (registry version `1`, stage `Production`) — this is the same identity returned by the API's `/version` endpoint and reported by `/api/2.0/mlflow/registered-models/search`.

This model choice balanced three needs:

- It beat the deterministic baseline on PR-AUC while staying simple enough to explain and debug.
- It is lightweight enough to keep inference latency comfortably inside the service SLO.
- Its inputs are engineered upstream, so the API boundary is intentionally narrow: `/predict` accepts post-featurization rows rather than raw ticks.

## Why This Architecture
We chose the current architecture because it matches the operational story we needed to prove in the team project:

- Kafka decouples ingestion from feature engineering and serving.
- FastAPI gives a small, testable prediction surface.
- MLflow makes the promoted model artifact explicit and inspectable.
- Prometheus and Grafana make latency, error rate, variant toggles, and freshness observable.
- Docker Compose lets the whole stack run reproducibly for grading and demos.

## Trade-offs
- Logistic Regression is less expressive than more complex sequence models, but it is faster to ship, easier to interpret, and easier to roll back safely.
- Replay is the default mode because reproducibility matters for grading and smoke tests, even though live Coinbase ingestion is also supported.
- The API does not accept raw ticks by design. That keeps serving simple, but it means the featurizer contract has to stay stable and well documented.

## Future Improvements
- Add richer microstructure signals such as order-book depth if a higher-fidelity feed becomes available.
- Automate alerting and retraining triggers on top of the existing monitoring and drift analysis.
- Expand evaluation across longer time windows and additional market regimes.

## Conclusion
This system now demonstrates a full team-project deliverable rather than an interim stub: real-time ingestion, engineered-feature inference, versioned model serving, observability, and rollback all work together around one canonical 7-feature API contract.
