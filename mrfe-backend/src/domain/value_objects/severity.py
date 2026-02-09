"""Severity value object."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from src.domain.exceptions import DomainValidationError


class SeverityLevel(IntEnum):
    """Severity levels with natural ordering."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True, slots=True)
class Severity:
    """Immutable severity wrapper."""

    value: SeverityLevel

    @classmethod
    def from_string(cls, raw_value: str) -> "Severity":
        """Create a Severity from text."""
        try:
            return cls(value=SeverityLevel[raw_value.strip().upper()])
        except KeyError as exc:
            raise DomainValidationError(f"unsupported severity: {raw_value}") from exc

    def __str__(self) -> str:
        """Return severity label."""
        return self.value.name
