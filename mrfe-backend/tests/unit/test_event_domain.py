"""Unit tests for Event aggregate."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.domain.entities.event import Event
from src.domain.exceptions import DomainValidationError
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


def test_event_create_emits_domain_event() -> None:
    """Ensure Event.create emits EventDetected."""
    event = Event.create(
        event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
        severity=Severity.from_string("MEDIUM"),
        confidence=Confidence(0.8),
        title="Earnings surprise",
        description="Company beat guidance",
        source="wire",
        impact_assets=("AAPL",),
    )
    domain_events = event.pull_domain_events()
    assert len(domain_events) == 1
    assert domain_events[0].name == "event.detected"


def test_event_rejects_empty_assets() -> None:
    """Validate invariant for impacted assets."""
    with pytest.raises(DomainValidationError):
        Event.create(
            event_type=EventType.from_string("MACRO_ECONOMIC"),
            severity=Severity.from_string("LOW"),
            confidence=Confidence(0.7),
            title="Macro update",
            description="Economy update",
            source="fed",
            impact_assets=(),
        )


@given(st.floats(min_value=0.0, max_value=1.0))
def test_confidence_range_valid(confidence: float) -> None:
    """Property test for confidence range."""
    confidence_vo = Confidence(confidence)
    assert 0.0 <= confidence_vo.value <= 1.0
