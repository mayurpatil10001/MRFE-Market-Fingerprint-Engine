"""Event aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Sequence

from src.domain.events import DomainEvent, EventClassified, EventDetected
from src.domain.exceptions import DomainValidationError
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


@dataclass(slots=True)
class Event:
    """Market event aggregate root with invariants and behavior."""

    event_id: EventId
    event_type: EventType
    severity: Severity
    confidence: Confidence
    title: str
    description: str
    source: str
    detected_at: datetime
    impact_assets: tuple[str, ...]
    market_sector: str | None = None
    country: str | None = None
    sentiment_score: float | None = None
    is_active: bool = True
    resolved_at: datetime | None = None
    version: int = 1
    _domain_events: list[DomainEvent] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        """Validate aggregate invariants."""
        if not self.title.strip():
            raise DomainValidationError("event title must not be empty")
        if not self.description.strip():
            raise DomainValidationError("event description must not be empty")
        if len(self.source.strip()) < 3:
            raise DomainValidationError("event source must be at least 3 characters")
        if self.detected_at.tzinfo is None:
            raise DomainValidationError("detected_at must be timezone-aware")
        if self.sentiment_score is not None and (
            self.sentiment_score < -1.0 or self.sentiment_score > 1.0
        ):
            raise DomainValidationError("sentiment_score must be between -1.0 and 1.0")
        if self.resolved_at is not None and self.resolved_at < self.detected_at:
            raise DomainValidationError("resolved_at cannot be earlier than detected_at")
        if len(self.impact_assets) == 0:
            raise DomainValidationError("at least one impact asset is required")
        if self.version < 1:
            raise DomainValidationError("version must be >= 1")

    @classmethod
    def create(
        cls,
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
    ) -> "Event":
        """Create a new event and emit detection domain event."""
        instance = cls(
            event_id=EventId.new(),
            event_type=event_type,
            severity=severity,
            confidence=confidence,
            title=title,
            description=description,
            source=source,
            detected_at=datetime.now(tz=timezone.utc),
            impact_assets=tuple(sorted({asset.upper() for asset in impact_assets})),
            market_sector=market_sector,
            country=country,
            sentiment_score=sentiment_score,
        )
        instance._domain_events.append(
            EventDetected.from_event(
                event_id=instance.event_id,
                event_type=str(instance.event_type),
                source=instance.source,
            )
        )
        return instance

    def classify(self, severity: Severity, confidence: Confidence) -> None:
        """Update classification details and emit classification event."""
        if not self.is_active:
            raise DomainValidationError("cannot classify inactive event")
        if confidence.value < 0.05:
            raise DomainValidationError("confidence too low for classification")
        self.severity = severity
        self.confidence = confidence
        self.version += 1
        self._domain_events.append(
            EventClassified.from_event(
                event_id=self.event_id,
                severity=str(severity),
                confidence=confidence.value,
            )
        )

    def add_impact_asset(self, asset_symbol: str) -> None:
        """Attach additional impacted asset."""
        normalized = asset_symbol.strip().upper()
        if not normalized:
            raise DomainValidationError("asset symbol cannot be empty")
        if normalized in self.impact_assets:
            return
        self.impact_assets = tuple(sorted((*self.impact_assets, normalized)))
        self.version += 1

    def deactivate(self) -> None:
        """Mark event as inactive."""
        if not self.is_active:
            return
        self.is_active = False
        self.resolved_at = datetime.now(tz=timezone.utc)
        self.version += 1

    def pull_domain_events(self) -> list[DomainEvent]:
        """Drain and return domain events for publication."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
