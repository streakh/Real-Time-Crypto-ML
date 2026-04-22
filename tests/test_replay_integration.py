"""
End-to-end replay integration test.

Verifies the full pipeline: ingestor → Kafka → featurizer → ticks.features → /predict.
Requires the full docker compose stack to be running already.

Run locally:
    docker compose up -d
    pytest tests/test_replay_integration.py -v
"""

import json
import time
import uuid

import pytest
import requests
from confluent_kafka import Consumer, KafkaException

BASE_URL = "http://localhost:8000"
KAFKA_BOOTSTRAP = "localhost:9092"
FEATURES_TOPIC = "ticks.features"

# The 7 fields the API's /predict endpoint requires
FEATURE_COLS = [
    "log_return",
    "spread_bps",
    "vol_60s",
    "mean_return_60s",
    "trade_intensity_60s",
    "n_ticks_60s",
    "spread_mean_60s",
]


def _api_healthy() -> bool:
    # Return True if the API is already up and healthy
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=2)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except Exception:
        return False


def _wait_for_api(timeout: int = 60) -> None:
    # Poll /health every 2 seconds until healthy or timeout
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _api_healthy():
            return
        time.sleep(2)
    raise RuntimeError(
        f"API at {BASE_URL} did not become healthy within {timeout}s. "
        "Start the repo stack first with `docker compose up -d` and wait for "
        "`curl http://localhost:8000/health` to return ok."
    )


@pytest.fixture(scope="module", autouse=True)
def stack_ready():
    # CI starts the stack explicitly; local runs should do the same.
    _wait_for_api(timeout=120)
    yield


def test_replay_pipeline_produces_features_and_scores():
    """
    Consume one message from ticks.features, send its fields to /predict,
    and assert the response is a valid score between 0 and 1.
    """
    # Use a unique group ID so each test run reads from the earliest offset
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": f"test-replay-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )

    try:
        consumer.subscribe([FEATURES_TOPIC])

        # Default replay speed is slower than CI, so allow enough time for the
        # first full 60-second feature window to be produced after startup.
        deadline = time.monotonic() + 180
        feature_msg = None

        while time.monotonic() < deadline:
            msg = consumer.poll(timeout=2.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())
            feature_msg = json.loads(msg.value())
            break

        assert feature_msg is not None, (
            f"No messages arrived on '{FEATURES_TOPIC}' within 180s. "
            "Check that the replay stack is healthy and producing features. "
            "CI speeds this up with REPLAY_SPEED=50, but the test should also "
            "pass against the default replay once startup has completed."
        )

        # Extract only the 7 fields the API needs
        missing = [c for c in FEATURE_COLS if c not in feature_msg]
        assert not missing, (
            f"Feature message is missing required fields: {missing}. "
            f"Message keys: {list(feature_msg.keys())}"
        )
        row = {col: feature_msg[col] for col in FEATURE_COLS}

        # Send to /predict and validate the response
        r = requests.post(f"{BASE_URL}/predict", json={"rows": [row]}, timeout=10)
        assert r.status_code == 200, f"/predict returned {r.status_code}: {r.text}"

        body = r.json()
        assert "scores" in body, "Response missing 'scores'"
        assert "model_variant" in body, "Response missing 'model_variant'"
        assert "version" in body, "Response missing 'version'"
        assert "ts" in body, "Response missing 'ts'"
        assert len(body["scores"]) == 1, f"Expected 1 score, got {len(body['scores'])}"
        score = body["scores"][0]
        assert isinstance(score, float), f"Score is not a float: {score!r}"
        assert 0.0 <= score <= 1.0, f"Score {score} is outside [0, 1]"

    finally:
        # Always close the consumer to release the group membership
        consumer.close()
