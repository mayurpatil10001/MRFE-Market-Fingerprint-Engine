"""Domain exception hierarchy for MRFE."""

from __future__ import annotations


class DomainError(Exception):
    """Base exception for all domain errors."""


class DomainValidationError(DomainError):
    """Raised when a domain invariant is violated."""


class DomainNotFoundError(DomainError):
    """Raised when a domain object cannot be found."""


class EventNotFoundError(DomainNotFoundError):
    """Raised when an event cannot be found."""


class FingerprintNotFoundError(DomainNotFoundError):
    """Raised when a fingerprint cannot be found."""


class ForecastNotFoundError(DomainNotFoundError):
    """Raised when a forecast cannot be found."""


class ConcurrencyConflictError(DomainError):
    """Raised when optimistic locking detects stale writes."""


class DuplicateEntityError(DomainError):
    """Raised when attempting to persist a duplicate entity."""
