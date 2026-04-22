"""Pytest fixtures for the FastAPI prediction service tests."""

import os

import pytest

# Point to the host-side pickle before api.main is imported; inside Docker the
# Dockerfile copies handoff/models/artifacts/ → models/artifacts/ so the default
# MODEL_PATH works there, but on the host the canonical location is handoff/.
os.environ.setdefault("MODEL_PATH", "handoff/models/artifacts/lr_pipeline.pkl")
# Force the pickle fallback in CI / local test runs where MLflow isn't running.
os.environ.setdefault("MLFLOW_TRACKING_URI", "http://localhost:99999")

from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
