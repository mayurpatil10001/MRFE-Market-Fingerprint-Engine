"""Event specification predicates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.domain.entities.event import Event
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


class Specification(Protocol):
    """Boolean specification protocol."""

    def is_satisfied_by(self, candidate: Event) -> bool:
        """Evaluate candidate against this specification."""


@dataclass(frozen=True, slots=True)
class EventSpecification:
    """Composable specification for event search."""

    event_type: EventType | None = None
    min_severity: Severity | None = None
    source: str | None = None
    is_active: bool | None = None
    detected_after: datetime | None = None
    detected_before: datetime | None = None

    def is_satisfied_by(self, candidate: Event) -> bool:
        """Evaluate event against configured filters."""
        if self.event_type is not None and candidate.event_type != self.event_type:
            return False
        if self.min_severity is not None and candidate.severity.value < self.min_severity.value:
            return False
        if self.source is not None and candidate.source != self.source:
            return False
        if self.is_active is not None and candidate.is_active != self.is_active:
            return False
        if self.detected_after is not None and candidate.detected_at <= self.detected_after:
            return False
        if self.detected_before is not None and candidate.detected_at >= self.detected_before:
            return False
        return True
