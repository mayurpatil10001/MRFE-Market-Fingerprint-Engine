"""Factory for Event aggregate creation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from src.domain.entities.event import Event
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


@dataclass(frozen=True, slots=True)
class EventFactory:
    """Factory that centralizes event construction rules."""

    @staticmethod
    def create(
        event_type: EventType,
        severity: Severity,
        confidence: Confidence,
        title: str,
        description: str,
        source: str,
        impact_assets: Sequence[str],
        market_sector: str | None = None,
        country: str | None = None,
        sentiment_score: float | None = None,
    ) -> Event:
        """Create a new event aggregate instance."""
        return Event.create(
            event_type=event_type,
            severity=severity,
            confidence=confidence,
            title=title,
            description=description,
            source=source,
            impact_assets=impact_assets,
            market_sector=market_sector,
            country=country,
            sentiment_score=sentiment_score,
        )
