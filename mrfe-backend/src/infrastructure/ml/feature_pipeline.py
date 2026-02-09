"""Feature engineering primitives for advanced ML inference paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint


@dataclass(frozen=True, slots=True)
class ForecastFeatureVector:
    """Normalized feature vector for forecast models."""

    sentiment_signal: float
    reaction_intensity: float
    volatility_impact: float
    volume_impact: float
    event_confidence: float
    fingerprint_confidence: float
    horizon_factor: float
    sector_risk: float

    def as_list(self) -> list[float]:
        """Return ordered float list."""
        return [
            self.sentiment_signal,
            self.reaction_intensity,
            self.volatility_impact,
            self.volume_impact,
            self.event_confidence,
            self.fingerprint_confidence,
            self.horizon_factor,
            self.sector_risk,
        ]


class MarketFeaturePipeline:
    """Build deterministic engineered features from domain aggregates."""

    _sector_risk_map: Mapping[str, float] = {
        "technology": 0.72,
        "financials": 0.58,
        "energy": 0.64,
        "healthcare": 0.47,
        "utilities": 0.31,
    }

    def build_forecast_features(
        self,
        event: Event,
        fingerprint: Fingerprint,
        forecast_horizon_hours: int,
    ) -> ForecastFeatureVector:
        """Construct bounded model features for forecast inference."""
        market_sector = (event.market_sector or "").strip().lower()
        sector_risk = self._sector_risk_map.get(market_sector, 0.5)
        sentiment_signal = float(event.sentiment_score or 0.0)
        horizon_factor = min(1.0, forecast_horizon_hours / 72.0)
        return ForecastFeatureVector(
            sentiment_signal=max(-1.0, min(1.0, sentiment_signal)),
            reaction_intensity=min(1.0, max(0.0, fingerprint.reaction_intensity)),
            volatility_impact=min(1.0, max(0.0, fingerprint.volatility_impact)),
            volume_impact=min(1.0, max(0.0, fingerprint.volume_impact / 2.0)),
            event_confidence=min(1.0, max(0.0, event.confidence.value)),
            fingerprint_confidence=min(1.0, max(0.0, fingerprint.confidence.value)),
            horizon_factor=horizon_factor,
            sector_risk=sector_risk,
        )
