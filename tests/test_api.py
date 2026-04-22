"""Smoke tests for the FastAPI prediction service."""

import json
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"

SAMPLE_ROW = {
    "log_return": 0.0001,
    "spread_bps": 1.5,
    "vol_60s": 0.00005,
    "mean_return_60s": 0.0,
    "trade_intensity_60s": 10.0,
    "n_ticks_60s": 50,
    "spread_mean_60s": 1.2,
}


def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_version(client):
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    # Required fields always present in the new shape
    assert "model" in body
    assert "sha" in body
    assert "source" in body
    assert "run_id" in body
    assert "stage" in body


def test_version_source(client):
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    # source must be one of the two known load paths — never empty
    assert body["source"] in ("mlflow", "pickle")
    # run_id is allowed to be null when MLflow is not available in CI
    assert "run_id" in body
    assert "stage" in body


def test_predict_single():
    r = requests.post(f"{BASE_URL}/predict", json={"rows": [SAMPLE_ROW]})
    assert r.status_code == 200
    body = r.json()
    assert len(body["scores"]) == 1
    assert 0.0 <= body["scores"][0] <= 1.0
    assert body["model_variant"] == "ml"


def test_predict_batch():
    r = requests.post(f"{BASE_URL}/predict", json={"rows": [SAMPLE_ROW] * 5})
    assert r.status_code == 200
    assert len(r.json()["scores"]) == 5


def test_predict_missing_field():
    bad_row = {"log_return": 0.0001}  # missing 6 fields
    r = requests.post(f"{BASE_URL}/predict", json={"rows": [bad_row]})
    assert r.status_code == 422


def test_metrics():
    r = requests.get(f"{BASE_URL}/metrics")
    assert r.status_code == 200
    assert "predict_requests_total" in r.text


def test_sample_json_payload(client):
    sample_path = Path(__file__).parent.parent / "handoff" / "data_sample" / "sample.json"
    with open(sample_path) as f:
        payload = json.load(f)

    response = client.post("/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "scores" in data
    assert "model_variant" in data
    assert "version" in data
    assert "ts" in data
    assert data["version"] == "v1.0"
    assert isinstance(data["scores"], list)
    assert len(data["scores"]) == 1
    assert 0 <= data["scores"][0] <= 1


if __name__ == "__main__":
    tests = [
        test_health,
        test_version,
        test_version_source,
        test_predict_single,
        test_predict_batch,
        test_predict_missing_field,
        test_metrics,
    ]
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
