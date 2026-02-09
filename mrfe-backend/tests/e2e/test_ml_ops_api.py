"""E2E tests for advanced MLOps endpoints."""

from __future__ import annotations


def _token(client) -> str:
    response = client.post("/api/v1/auth/token", json={"user_id": "mlops_user", "roles": ["trader"]})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_model_registry_register_list_promote(client) -> None:
    """Register, list, and promote a model via API."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    register = client.post(
        "/api/v1/ml/models/register",
        headers=headers,
        json={
            "name": "forecast-ensemble",
            "version": "2026.02.07",
            "framework": "pytorch",
            "artifact_uri": "s3://mrfe/models/forecast-ensemble/2026.02.07",
            "tags": {"owner": "quant-research", "risk_class": "medium"},
        },
    )
    assert register.status_code == 200
    model_id = register.json()["model_id"]

    listing = client.get("/api/v1/ml/models", headers=headers)
    assert listing.status_code == 200
    assert any(item["model_id"] == model_id for item in listing.json())

    promoted = client.post(
        f"/api/v1/ml/models/{model_id}/promote",
        headers=headers,
        json={"stage": "production"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["stage"] == "production"


def test_drift_check_returns_report(client) -> None:
    """Return deterministic drift report payload."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/ml/drift/check",
        headers=headers,
        json={
            "model_version": "2026.02.07",
            "baseline_distribution": {"negative": 0.2, "neutral": 0.6, "positive": 0.2},
            "live_distribution": {"negative": 0.22, "neutral": 0.56, "positive": 0.22},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"stable", "watch", "drift_alert"}
    assert payload["drift_score"] >= 0.0
    assert isinstance(payload["retrain_queued"], bool)


def test_continuous_learning_endpoints(client) -> None:
    """Exercise incremental learning, regime detection, and retraining schedule endpoints."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    update = client.post(
        "/api/v1/ml/learning/incremental-update",
        headers=headers,
        json={"vector": [0.1, 0.2, 0.3, 0.4, 0.2, 0.1, 0.0, 0.5]},
    )
    assert update.status_code == 200
    assert update.json()["observations"] >= 1

    regime = client.post(
        "/api/v1/ml/regime/detect",
        headers=headers,
        json={"returns": [0.01, -0.002, 0.004, -0.001, 0.003]},
    )
    assert regime.status_code == 200
    assert regime.json()["regime"] in {"bull", "bear", "volatile", "sideways", "unknown"}

    schedule = client.get("/api/v1/ml/retraining/schedule", headers=headers)
    assert schedule.status_code == 200
    assert isinstance(schedule.json()["due"], bool)
