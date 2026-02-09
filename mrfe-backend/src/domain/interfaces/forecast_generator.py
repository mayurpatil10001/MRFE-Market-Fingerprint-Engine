"""Port for forecast generation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint


@dataclass(frozen=True, slots=True)
class ForecastGenerationResult:
    """Result payload used to build forecast entity."""

    probability_distribution: dict[str, float]
    predicted_movement: float
    confidence: float
    risk_metrics: dict[str, float]


class ForecastGenerator(Protocol):
    """Port for forecast-generation algorithms."""

    async def generate(
        self,
        event: Event,
        fingerprint: Fingerprint,
        asset_symbol: str,
        forecast_horizon_hours: int,
        model_version: str,
    ) -> ForecastGenerationResult:
        """Generate raw output used to create forecast entity."""
