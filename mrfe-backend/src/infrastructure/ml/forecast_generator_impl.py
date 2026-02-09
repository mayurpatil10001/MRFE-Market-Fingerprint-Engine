"""Forecast generation strategy implementations."""

from __future__ import annotations

import math

from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.interfaces import ForecastGenerationResult, ForecastGenerator


class QuantForecastGenerator(ForecastGenerator):
    """Baseline probabilistic forecast strategy."""

    async def generate(
        self,
        event: Event,
        fingerprint: Fingerprint,
        asset_symbol: str,
        forecast_horizon_hours: int,
        model_version: str,
    ) -> ForecastGenerationResult:
        """Generate forecast outputs from event and fingerprint features."""
        intensity = fingerprint.reaction_intensity
        signed_signal = (event.sentiment_score or 0.0) * intensity
        movement = max(-1.0, min(1.0, round(signed_signal, 4)))
        neutral = max(0.1, 1.0 - abs(movement))
        directional = 1.0 - neutral
        positive = directional if movement >= 0 else 0.0
        negative = directional if movement < 0 else 0.0
        probability_distribution = {
            "strong_negative": round(negative * 0.35, 4),
            "negative": round(negative * 0.65, 4),
            "neutral": round(neutral, 4),
            "positive": round(positive * 0.65, 4),
            "strong_positive": round(positive * 0.35, 4),
        }
        total = sum(probability_distribution.values())
        normalized = {key: round(value / total, 4) for key, value in probability_distribution.items()}
        confidence = min(0.99, max(0.1, (event.confidence.value + fingerprint.confidence.value) / 2))
        risk_metrics = {
            "volatility_attribution": round(min(1.0, fingerprint.volatility_impact), 4),
            "liquidity_risk": round(min(1.0, math.log1p(fingerprint.volume_impact) / 2), 4),
            "model_uncertainty": round(1 - confidence, 4),
            "event_specific_risk": round(min(1.0, intensity * 0.8), 4),
        }
        return ForecastGenerationResult(
            probability_distribution=normalized,
            predicted_movement=movement,
            confidence=confidence,
            risk_metrics=risk_metrics,
        )
