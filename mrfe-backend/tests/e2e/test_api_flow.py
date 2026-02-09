"""End-to-end API test for critical flow."""

from __future__ import annotations


def _token(client) -> str:
    response = client.post("/api/v1/auth/token", json={"user_id": "u1", "roles": ["trader"]})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_detect_and_get_event(client) -> None:
    """Detect event then read it back."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    detect = client.post(
        "/api/v1/events/detect",
        json={
            "news_content": "Acquisition agreement announced by company with expected synergies.",
            "source": "wire",
        },
        headers=headers,
    )
    assert detect.status_code == 200
    payload = detect.json()
    assert payload
    event_id = payload[0]["event_id"]
    get_event = client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert get_event.status_code == 200
    assert get_event.json()["event_id"] == event_id


def test_classify_list_and_measure_reaction_flow(client) -> None:
    """Classify event, generate artifacts, list them, and measure reaction."""
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    classify = client.post(
        "/api/v1/events/classify",
        json={
            "title": "Company announces acquisition deal",
            "description": "The company announced a strategic acquisition expected to close next quarter.",
            "source": "desk",
        },
        headers=headers,
    )
    assert classify.status_code == 200
    event_id = classify.json()["event_id"]

    fingerprint = client.post(
        "/api/v1/fingerprints",
        json={
            "event_id": event_id,
            "asset_symbol": "AAPL",
            "model_version": "v2",
        },
        headers=headers,
    )
    assert fingerprint.status_code == 200
    fingerprint_id = fingerprint.json()["fingerprint_id"]

    forecast = client.post(
        "/api/v1/forecasts",
        json={
            "event_id": event_id,
            "fingerprint_id": fingerprint_id,
            "asset_symbol": "AAPL",
            "forecast_horizon_hours": 24,
            "model_version": "v2",
        },
        headers=headers,
    )
    assert forecast.status_code == 200

    list_fingerprints = client.get(
        f"/api/v1/fingerprints?event_id={event_id}",
        headers=headers,
    )
    assert list_fingerprints.status_code == 200
    assert list_fingerprints.json()["total"] >= 1

    list_forecasts = client.get(
        "/api/v1/forecasts?asset_symbol=AAPL",
        headers=headers,
    )
    assert list_forecasts.status_code == 200
    assert list_forecasts.json()["total"] >= 1

    reaction = client.post(
        "/api/v1/reactions/measure",
        json={
            "event_id": event_id,
            "asset_symbol": "AAPL",
            "pre_event_price": 100.0,
            "post_event_price": 103.5,
            "pre_event_volume": 1_000_000,
            "post_event_volume": 1_700_000,
            "pre_event_volatility": 0.18,
            "post_event_volatility": 0.25,
            "horizon_minutes": 60,
        },
        headers=headers,
    )
    assert reaction.status_code == 200
    payload = reaction.json()
    assert 0.0 <= payload["reaction_intensity"] <= 1.0

    persisted = client.post(
        "/api/v1/reactions/measure-and-store",
        json={
            "event_id": event_id,
            "asset_symbol": "AAPL",
            "pre_event_price": 100.0,
            "post_event_price": 101.2,
            "pre_event_volume": 1_000_000,
            "post_event_volume": 1_100_000,
            "pre_event_volatility": 0.2,
            "post_event_volatility": 0.24,
            "horizon_minutes": 30,
        },
        headers=headers,
    )
    assert persisted.status_code == 200

    listed = client.get("/api/v1/reactions?asset_symbol=AAPL", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


def test_service_api_key_auth_allows_protected_route(client) -> None:
    """Configured service API key should authorize protected endpoints."""
    from src.core.config.settings import settings

    previous = settings.service_api_keys_csv
    settings.service_api_keys_csv = "svc-test-key"
    try:
        response = client.post(
            "/api/v1/events/detect",
            headers={"X-API-Key": "svc-test-key"},
            json={
                "news_content": "Merger transaction announced with expected regulatory review and synergy upside.",
                "source": "wire",
            },
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        settings.service_api_keys_csv = previous
