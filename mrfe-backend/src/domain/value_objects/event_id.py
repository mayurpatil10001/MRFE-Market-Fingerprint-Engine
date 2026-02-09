"""Event identifier value object."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class EventId:
    """Immutable event identifier."""

    value: UUID

    @classmethod
    def new(cls) -> "EventId":
        """Create a new random event identifier."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, raw_value: str) -> "EventId":
        """Create an EventId from a UUID string."""
        try:
            return cls(value=UUID(raw_value))
        except ValueError as exc:
            raise DomainValidationError("event_id must be a valid UUID") from exc

    def __str__(self) -> str:
        """Return the canonical UUID string."""
        return str(self.value)
