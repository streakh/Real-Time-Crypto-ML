"""
BTC Volatility Spike Detector — FastAPI Service

Loads the trained Logistic Regression pipeline and serves predictions
via a REST API with /health, /predict, /version, and /metrics endpoints.

Supports a rollback toggle via MODEL_VARIANT=ml|baseline:
  - ml       (default) — sklearn LR pipeline; score = predict_proba[:, 1]
  - baseline           — deterministic z-style rule on vol_60s vs threshold
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
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from starlette.responses import Response

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MODEL_PATH = os.getenv("MODEL_PATH", "models/artifacts/lr_pipeline.pkl")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1.0")
MODEL_VARIANT = os.getenv("MODEL_VARIANT", "ml").lower()
BASELINE_VOL_THRESHOLD = float(os.getenv("BASELINE_VOL_THRESHOLD", "0.000048"))

if MODEL_VARIANT not in {"ml", "baseline"}:
    raise ValueError(f"MODEL_VARIANT must be 'ml' or 'baseline', got {MODEL_VARIANT!r}")

# ---------------------------------------------------------------------------
# Load model at startup — only required for MODEL_VARIANT=ml.
# Baseline must be able to start without the ML artifact, otherwise the
# rollback path is useless in the exact failure mode it exists to handle
# (model file missing/corrupt).
# ---------------------------------------------------------------------------
FEATURE_COLS_DEFAULT = [
    "log_return",
    "spread_bps",
    "vol_60s",
    "mean_return_60s",
    "trade_intensity_60s",
    "n_ticks_60s",
    "spread_mean_60s",
]

PIPELINE = None
FEATURE_COLS = FEATURE_COLS_DEFAULT
TAU: float | None = None

if MODEL_VARIANT == "ml":
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
    GIT_SHA = os.getenv("GIT_SHA", "unknown")

# ---------------------------------------------------------------------------
# Prometheus metrics — labelled by model_variant so panels can split / overlay
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "predict_requests_total",
    "Total prediction requests",
    ["model_variant"],
)
REQUEST_ERRORS = Counter(
    "predict_errors_total",
    "Total failed prediction requests",
    ["model_variant"],
)
REQUEST_LATENCY = Histogram(
    "predict_latency_seconds",
    "Prediction request latency in seconds",
    ["model_variant"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.8, 1.0],
)
ACTIVE_VARIANT = Gauge(
    "model_variant_active",
    "Currently active model variant (1 = active)",
    ["model_variant"],
)
ACTIVE_VARIANT.labels(model_variant=MODEL_VARIANT).set(1)

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
# Scoring backends
# ---------------------------------------------------------------------------


def _score_ml(rows: list[TickRow]) -> list[float]:
    X = np.array([[getattr(row, col) for col in FEATURE_COLS] for row in rows])
    y_prob = PIPELINE.predict_proba(X)[:, 1]
    return [round(float(p), 6) for p in y_prob]


def _score_baseline(rows: list[TickRow]) -> list[float]:
    # Mirrors the labeling rule: a tick is "spiking" when its 60s realised
    # volatility exceeds the same threshold used to generate training labels.
    # Returns 1.0 / 0.0 so the response shape stays compatible with /predict.
    return [1.0 if row.vol_60s > BASELINE_VOL_THRESHOLD else 0.0 for row in rows]


SCORERS = {"ml": _score_ml, "baseline": _score_baseline}


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
        "variant": MODEL_VARIANT,
        "sha": GIT_SHA,
        "tau": TAU,
        "baseline_vol_threshold": BASELINE_VOL_THRESHOLD,
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
    REQUEST_COUNT.labels(model_variant=MODEL_VARIANT).inc()
    start = time.perf_counter()

    try:
        scores = SCORERS[MODEL_VARIANT](req.rows)
        return PredictResponse(
            scores=scores,
            model_variant=MODEL_VARIANT,
            version=MODEL_VERSION,
            ts=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as exc:
        REQUEST_ERRORS.labels(model_variant=MODEL_VARIANT).inc()
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        REQUEST_LATENCY.labels(model_variant=MODEL_VARIANT).observe(
            time.perf_counter() - start
        )
