"""Unit of Work contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.domain.interfaces.event_repository import EventRepository
from src.domain.interfaces.fingerprint_repository import FingerprintRepository
from src.domain.interfaces.forecast_repository import ForecastRepository


@runtime_checkable
class UnitOfWork(Protocol):
    """Transaction boundary contract."""

    events: EventRepository
    fingerprints: FingerprintRepository
    forecasts: ForecastRepository

    async def __aenter__(self) -> "UnitOfWork":
        """Open transaction."""

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Commit or rollback transaction."""

    async def commit(self) -> None:
        """Persist transaction."""

    async def rollback(self) -> None:
        """Rollback transaction."""
