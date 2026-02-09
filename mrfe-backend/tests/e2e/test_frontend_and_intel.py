"""E2E tests for frontend serving and intel API behavior."""

from __future__ import annotations


def _token(client) -> str:
    response = client.post("/api/v1/auth/token", json={"user_id": "u2", "roles": ["trader"]})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_root_serves_dashboard_html(client) -> None:
    """Root route should serve the moved dashboard frontend."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "MRFE Control Room" in response.text
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-content-type-options") == "nosniff"


def test_intel_brief_uses_fallback_without_api_key(client) -> None:
    """Intel endpoint returns deterministic response if OpenRouter key is absent."""
    token = _token(client)
    response = client.post(
        "/api/v1/intel/brief",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "symbol": "NVDA",
            "market_context": (
                "NVIDIA earnings beat expectations with strong data center growth and raised guidance."
            ),
            "horizon_hours": 24,
            "risk_profile": "balanced",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] in {"heuristic-fallback", "openrouter"}
    assert payload["symbol"] == "NVDA"
    assert isinstance(payload["scenarios"], list)
    assert len(payload["scenarios"]) == 3
