"""Locust load test scenario."""

from __future__ import annotations

from locust import HttpUser, between, task


class MRFEUser(HttpUser):
    """Simulated API user."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        response = self.client.post("/api/v1/auth/token", json={"user_id": "load-user", "roles": ["reader"]})
        self.token = response.json().get("access_token", "")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(2)
    def health(self) -> None:
        self.client.get("/api/v1/health/live")

    @task(1)
    def detect_event(self) -> None:
        self.client.post(
            "/api/v1/events/detect",
            headers=self.headers,
            json={
                "news_content": "Earnings report showed strong margin expansion and raised guidance.",
                "source": "wire",
            },
        )
