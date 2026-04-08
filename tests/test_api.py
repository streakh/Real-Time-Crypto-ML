"""Smoke tests for the FastAPI prediction service."""

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


def test_version():
    r = requests.get(f"{BASE_URL}/version")
    assert r.status_code == 200
    body = r.json()
    assert "model" in body
    assert "sha" in body
    assert "tau" in body
    assert len(body["features"]) == 7


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


if __name__ == "__main__":
    tests = [
        test_health,
        test_version,
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
