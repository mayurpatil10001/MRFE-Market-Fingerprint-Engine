"""Confidence value object."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class Confidence:
    """Immutable confidence value in [0.0, 1.0]."""

    value: float

    def __post_init__(self) -> None:
        """Validate confidence range."""
        if self.value < 0.0 or self.value > 1.0:
            raise DomainValidationError("confidence must be between 0.0 and 1.0")

    @classmethod
    def from_percentage(cls, percentage: float) -> "Confidence":
        """Create confidence from percent range [0, 100]."""
        if percentage < 0.0 or percentage > 100.0:
            raise DomainValidationError("percentage must be between 0 and 100")
        return cls(value=round(percentage / 100.0, 6))

    def __float__(self) -> float:
        """Return raw float value."""
        return self.value
