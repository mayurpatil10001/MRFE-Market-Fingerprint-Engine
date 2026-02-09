"""Event type value object."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.domain.exceptions import DomainValidationError


class EventTypeCode(str, Enum):
    """Supported event categories."""

    EARNINGS_ANNOUNCEMENT = "EARNINGS_ANNOUNCEMENT"
    MERGER_ACQUISITION = "MERGER_ACQUISITION"
    REGULATORY_CHANGE = "REGULATORY_CHANGE"
    PRODUCT_LAUNCH = "PRODUCT_LAUNCH"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    LEGAL_ISSUE = "LEGAL_ISSUE"
    MACRO_ECONOMIC = "MACRO_ECONOMIC"
    GEO_POLITICAL = "GEO_POLITICAL"
    NATURAL_DISASTER = "NATURAL_DISASTER"
    TECHNICAL_BREACH = "TECHNICAL_BREACH"


@dataclass(frozen=True, slots=True)
class EventType:
    """Immutable event type wrapper."""

    value: EventTypeCode

    @classmethod
    def from_string(cls, raw_value: str) -> "EventType":
        """Create an EventType from case-insensitive text."""
        normalized = raw_value.strip().upper().replace(" ", "_")
        try:
            return cls(value=EventTypeCode(normalized))
        except ValueError as exc:
            raise DomainValidationError(f"unsupported event_type: {raw_value}") from exc

    def __str__(self) -> str:
        """Return normalized type value."""
        return self.value.value
