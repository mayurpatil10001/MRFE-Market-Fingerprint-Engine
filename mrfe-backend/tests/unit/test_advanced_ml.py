"""Unit tests for advanced ML infrastructure components."""

from __future__ import annotations

import pytest

from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.ml import (
    AdvancedEnsembleForecastGenerator,
    MarketFeaturePipeline,
    PopulationDriftDetector,
)


def _event() -> Event:
    return Event.create(
        event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
        severity=Severity.from_string("HIGH"),
        confidence=Confidence(0.84),
        title="Earnings beat with raised guidance",
        description="Institutional demand remains strong.",
        source="wire",
        impact_assets=("NVDA",),
        market_sector="technology",
        sentiment_score=0.64,
    )


def _fingerprint(event_id: EventId) -> Fingerprint:
    return Fingerprint.create(
        event_id=event_id,
        asset_symbol="NVDA",
        reaction_patterns={"shock": 0.52},
        baseline_metrics={"vol": 0.21},
        reaction_intensity=0.66,
        duration_minutes=180,
        volatility_impact=0.32,
        volume_impact=0.55,
        confidence=Confidence(0.78),
        model_version="v2",
    )


@pytest.mark.asyncio
async def test_ensemble_forecast_generator_outputs_valid_distribution() -> None:
    """Advanced ensemble generator should return normalized output."""
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    result = await AdvancedEnsembleForecastGenerator().generate(
        event=event,
        fingerprint=fingerprint,
        asset_symbol="NVDA",
        forecast_horizon_hours=24,
        model_version="v2",
    )
    assert -1.0 <= result.predicted_movement <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert abs(sum(result.probability_distribution.values()) - 1.0) <= 0.02
    assert "model_disagreement" in result.risk_metrics


def test_drift_detector_classifies_large_shift_as_alert() -> None:
    """Large distribution shift should be flagged as drift alert."""
    detector = PopulationDriftDetector()
    report = detector.evaluate(
        baseline_distribution={"negative": 0.1, "neutral": 0.8, "positive": 0.1},
        live_distribution={"negative": 0.7, "neutral": 0.2, "positive": 0.1},
        alert_threshold=0.1,
    )
    assert report.status == "drift_alert"
    assert report.drift_score >= 0.1


def test_feature_pipeline_bounds_values() -> None:
    """Feature pipeline should clamp numeric features to valid ranges."""
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    features = MarketFeaturePipeline().build_forecast_features(
        event=event,
        fingerprint=fingerprint,
        forecast_horizon_hours=240,
    )
    assert features.horizon_factor == 1.0
    assert 0.0 <= features.reaction_intensity <= 1.0
