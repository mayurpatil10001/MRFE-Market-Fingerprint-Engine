"""Additional domain-layer branch coverage tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.domain.aggregates.event_aggregate import EventAggregate
from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.entities.forecast import Forecast
from src.domain.exceptions import DomainValidationError
from src.domain.specifications import EventSpecification
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


def _event() -> Event:
    return Event.create(
        event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
        severity=Severity.from_string("MEDIUM"),
        confidence=Confidence(0.8),
        title="Earnings call",
        description="Company raised guidance",
        source="wire",
        impact_assets=("AAPL",),
        sentiment_score=0.2,
    )


def _fingerprint(event_id: EventId, asset: str = "AAPL") -> Fingerprint:
    return Fingerprint.create(
        event_id=event_id,
        asset_symbol=asset,
        reaction_patterns={"a": 0.1},
        baseline_metrics={"b": 0.2},
        reaction_intensity=0.4,
        duration_minutes=120,
        volatility_impact=0.3,
        volume_impact=0.4,
        confidence=Confidence(0.75),
        model_version="v1",
    )


def _forecast(event_id: EventId, fingerprint_id: EventId, asset: str = "AAPL") -> Forecast:
    return Forecast.create(
        event_id=event_id,
        fingerprint_id=fingerprint_id,
        asset_symbol=asset,
        forecast_horizon_hours=24,
        probability_distribution={
            "strong_negative": 0.1,
            "negative": 0.2,
            "neutral": 0.4,
            "positive": 0.2,
            "strong_positive": 0.1,
        },
        predicted_movement=0.2,
        confidence=Confidence(0.7),
        risk_metrics={"model_uncertainty": 0.2},
        model_version="v1",
    )


def test_event_classify_add_asset_and_deactivate() -> None:
    event = _event()
    event.classify(Severity.from_string("HIGH"), Confidence(0.9))
    event.add_impact_asset("msft")
    event.add_impact_asset("MSFT")
    event.deactivate()
    assert event.severity == Severity.from_string("HIGH")
    assert "MSFT" in event.impact_assets
    assert event.is_active is False
    assert event.resolved_at is not None
    assert any(item.name == "event.classified" for item in event.pull_domain_events())


def test_event_constructor_validation_branches() -> None:
    with pytest.raises(DomainValidationError):
        Event(
            event_id=EventId.new(),
            event_type=EventType.from_string("MACRO_ECONOMIC"),
            severity=Severity.from_string("LOW"),
            confidence=Confidence(0.2),
            title="x",
            description="y",
            source="a",
            detected_at=datetime.now(tz=timezone.utc),
            impact_assets=("SPY",),
        )
    with pytest.raises(DomainValidationError):
        Event(
            event_id=EventId.new(),
            event_type=EventType.from_string("MACRO_ECONOMIC"),
            severity=Severity.from_string("LOW"),
            confidence=Confidence(0.2),
            title="x",
            description="y",
            source="wire",
            detected_at=datetime.now(),
            impact_assets=("SPY",),
        )


def test_fingerprint_update_and_validation() -> None:
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    version_before = fingerprint.version
    fingerprint.update(reaction_intensity=0.8, volatility_impact=0.1, volume_impact=0.2)
    assert fingerprint.reaction_intensity == 0.8
    assert fingerprint.version == version_before + 1
    with pytest.raises(DomainValidationError):
        Fingerprint(
            fingerprint_id=EventId.new(),
            event_id=event.event_id,
            asset_symbol="AAPL",
            reaction_patterns={},
            baseline_metrics={},
            reaction_intensity=2.0,
            duration_minutes=1,
            volatility_impact=0.1,
            volume_impact=0.1,
            confidence=Confidence(0.5),
            model_version="v1",
            created_at=datetime.now(tz=timezone.utc),
            updated_at=datetime.now(tz=timezone.utc),
        )


def test_forecast_validation_and_expiry() -> None:
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    forecast = _forecast(event.event_id, fingerprint.fingerprint_id)
    assert forecast.is_expired() is False
    with pytest.raises(DomainValidationError):
        Forecast(
            forecast_id=EventId.new(),
            event_id=event.event_id,
            fingerprint_id=fingerprint.fingerprint_id,
            asset_symbol="AAPL",
            forecast_horizon_hours=24,
            probability_distribution={"up": 0.9},
            predicted_movement=0.1,
            confidence=Confidence(0.5),
            risk_metrics={},
            model_version="v1",
            created_at=datetime.now(tz=timezone.utc),
            expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        )


def test_event_aggregate_and_specification() -> None:
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    forecast = _forecast(event.event_id, fingerprint.fingerprint_id)
    aggregate = EventAggregate(event=event)
    aggregate.add_fingerprint(fingerprint)
    aggregate.add_forecast(forecast)
    with pytest.raises(DomainValidationError):
        aggregate.add_fingerprint(_fingerprint(event.event_id))
    spec = EventSpecification(
        event_type=event.event_type,
        min_severity=Severity.from_string("LOW"),
        source=event.source,
        is_active=True,
    )
    assert spec.is_satisfied_by(event) is True
    aggregate.deactivate()
    assert event.is_active is False


def test_value_object_validation_branches() -> None:
    with pytest.raises(DomainValidationError):
        EventId.from_string("not-a-uuid")
    with pytest.raises(DomainValidationError):
        Confidence.from_percentage(300)
    with pytest.raises(DomainValidationError):
        EventType.from_string("unknown")
    with pytest.raises(DomainValidationError):
        Severity.from_string("unknown")
