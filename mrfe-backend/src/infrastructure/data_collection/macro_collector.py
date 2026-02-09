"""Macro-economic data collector utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx


@dataclass(frozen=True, slots=True)
class MacroObservation:
    """One macro time-series observation."""

    series_id: str
    date: datetime
    value: float


class FREDMacroCollector:
    """Collector for FRED series observations using REST API."""

    _base_url = "https://api.stlouisfed.org/fred"

    def __init__(self, api_key: str, timeout_seconds: float = 20.0) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout_seconds, base_url=self._base_url)

    async def fetch_series(
        self,
        series_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[MacroObservation]:
        """Fetch one FRED series and normalize observations."""
        params = {
            "series_id": series_id,
            "api_key": self._api_key,
            "file_type": "json",
        }
        if start_date:
            params["observation_start"] = start_date
        if end_date:
            params["observation_end"] = end_date
        response = await self._client.get("/series/observations", params=params)
        response.raise_for_status()
        payload = response.json()
        raw_items = payload.get("observations", [])
        if not isinstance(raw_items, list):
            return []
        normalized: list[MacroObservation] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            parsed = self._to_observation(series_id=series_id, raw=item)
            if parsed is not None:
                normalized.append(parsed)
        return normalized

    @staticmethod
    def _to_observation(series_id: str, raw: dict[str, Any]) -> MacroObservation | None:
        date_raw = raw.get("date")
        value_raw = raw.get("value")
        if not isinstance(date_raw, str) or not isinstance(value_raw, str):
            return None
        if value_raw in {".", ""}:
            return None
        try:
            date = datetime.fromisoformat(date_raw).replace(tzinfo=UTC)
            value = float(value_raw)
        except ValueError:
            return None
        return MacroObservation(series_id=series_id, date=date, value=value)

    def to_postgres_rows(self, observations: list[MacroObservation]) -> list[dict[str, Any]]:
        """Map observations to PostgreSQL insert-ready row dicts."""
        return [
            {"series_id": item.series_id, "observed_at": item.date, "value": item.value}
            for item in observations
        ]

    async def close(self) -> None:
        """Close HTTP resources."""
        await self._client.aclose()
