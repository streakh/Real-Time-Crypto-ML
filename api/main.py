"""
BTC Volatility Spike Detector — FastAPI Service

Loads the trained Logistic Regression pipeline and serves predictions
via a REST API with /health, /predict, /version, and /metrics endpoints.
"""

import os
import pickle
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_PATH = os.getenv(
    "MODEL_PATH", "models/artifacts/lr_pipeline.pkl"
)
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0")

# ---------------------------------------------------------------------------
# Load model at startup
# ---------------------------------------------------------------------------
_model_path = Path(MODEL_PATH)
if not _model_path.exists():
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}")

with open(_model_path, "rb") as f:
    _bundle = pickle.load(f)

PIPELINE = _bundle["pipeline"]
FEATURE_COLS = _bundle["feature_cols"]
TAU = _bundle["tau"]

# ---------------------------------------------------------------------------
# Git SHA (resolved once at startup)
# ---------------------------------------------------------------------------
try:
    GIT_SHA = (
        subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
    )
except Exception:
    GIT_SHA = "unknown"

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "predict_requests_total",
    "Total prediction requests",
)
REQUEST_ERRORS = Counter(
    "predict_errors_total",
    "Total failed prediction requests",
)
REQUEST_LATENCY = Histogram(
    "predict_latency_seconds",
    "Prediction request latency in seconds",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.8, 1.0],
)

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TickRow(BaseModel):
    """A single observation with the 7 required features."""
    log_return: float
    spread_bps: float
    vol_60s: float
    mean_return_60s: float
    trade_intensity_60s: float
    n_ticks_60s: float
    spread_mean_60s: float


class PredictRequest(BaseModel):
    rows: list[TickRow]


class PredictResponse(BaseModel):
    scores: list[float]
    model_variant: str
    version: str
    ts: str

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="BTC Volatility Spike Detector")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    return {
        "model": "lr_pipeline",
        "version": MODEL_VERSION,
        "sha": GIT_SHA,
        "tau": TAU,
        "features": FEATURE_COLS,
    }


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    REQUEST_COUNT.inc()
    start = time.perf_counter()

    try:
        # Build feature matrix in the correct column order
        X = np.array(
            [[getattr(row, col) for col in FEATURE_COLS] for row in req.rows]
        )

        # Probability of class 1 (volatility spike)
        y_prob = PIPELINE.predict_proba(X)[:, 1]

        # Round scores for readability
        scores = [round(float(p), 6) for p in y_prob]

        return PredictResponse(
            scores=scores,
            model_variant="ml",
            version=MODEL_VERSION,
            ts=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        REQUEST_ERRORS.inc()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        REQUEST_LATENCY.observe(time.perf_counter() - start)
