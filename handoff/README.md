# BTC Volatility Spike Detector — Handoff Package (Reference Only)

This folder preserves the original Part 1 individual-assignment handoff for
reference, provenance, and compliance. It is not the runtime entrypoint for the
Part 2 team project.

## Runtime entrypoint for the team project

Start the system from the repo root only:

```bash
cp .env.example .env   # optional: override defaults
docker compose up -d
```

Use the root [`README.md`](../README.md) and root
[`docker-compose.yaml`](../docker-compose.yaml) for startup, health checks,
replay vs live mode, and rollback instructions. Do not run
`handoff/docker/compose.yaml` for the team project.

## Model Selection: Selected-Base

The deployed model is the **Logistic Regression pipeline** (`models/artifacts/lr_pipeline.pkl`), chosen as the selected-base model. It outperforms the z-score baseline on unseen test data (Test PR-AUC 0.1459 vs 0.1340) using a time-based evaluation split with no data leakage.

---

## Package Contents

```text
handoff/
├── docker/
│   ├── compose.yaml          Historical Part 1 compose artifact (do not run here)
│   ├── Dockerfile.ingestor   WebSocket ingestor container
│   └── .env.example          Environment variable template
├── docs/
│   ├── feature_spec.md       Feature definitions and label schema
│   └── model_card_v1.md      Model card
├── models/
│   └── artifacts/
│       └── lr_pipeline.pkl   Trained sklearn pipeline (tau = 0.7015)
├── data_sample/
│   ├── raw_slice.parquet     First 10 minutes of raw tick data
│   └── features_slice.csv    Corresponding labelled feature rows
├── reports/
│   ├── model_eval.pdf        Evaluation summary (Milestone 3)
│   ├── train_vs_test.html    Evidently drift report
│   └── predictions.csv       Full inference output [timestamp, y_true, y_prob, y_pred]
├── requirements.txt
└── README.md                 This file
```

---

## Sample curl for /predict

Once the root stack is running:

```bash
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Content-Type: application/json" \
  -d @handoff/data_sample/sample.json
```
