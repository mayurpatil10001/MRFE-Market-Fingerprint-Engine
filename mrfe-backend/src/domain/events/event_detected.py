"""Domain events for event lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.domain.value_objects.event_id import EventId


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base domain event."""

    name: str
    aggregate_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


@dataclass(frozen=True, slots=True)
class EventDetected(DomainEvent):
    """Raised when an event is created."""

    event_id: str = ""
    event_type: str = ""
    source: str = ""

    @classmethod
    def from_event(cls, event_id: EventId, event_type: str, source: str) -> "EventDetected":
        """Build event payload from aggregate values."""
        raw_event_id = str(event_id)
        return cls(
            name="event.detected",
            aggregate_id=raw_event_id,
            event_id=raw_event_id,
            event_type=event_type,
            source=source,
        )


@dataclass(frozen=True, slots=True)
class EventClassified(DomainEvent):
    """Raised when event severity/confidence is adjusted."""

    event_id: str = ""
    severity: str = ""
    confidence: float = 0.0

    @classmethod
    def from_event(
        cls,
        event_id: EventId,
        severity: str,
        confidence: float,
    ) -> "EventClassified":
        """Build event payload from aggregate values."""
        raw_event_id = str(event_id)
        return cls(
            name="event.classified",
            aggregate_id=raw_event_id,
            event_id=raw_event_id,
            severity=severity,
            confidence=confidence,
        )
