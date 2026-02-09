"""SQLAlchemy Unit of Work implementation."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.unit_of_work import UnitOfWork
from src.infrastructure.database.repositories.event_repository_impl import SQLAlchemyEventRepository
from src.infrastructure.database.repositories.fingerprint_repository_impl import (
    SQLAlchemyFingerprintRepository,
)
from src.infrastructure.database.repositories.forecast_repository_impl import (
    SQLAlchemyForecastRepository,
)


class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy transactional unit of work."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.events = SQLAlchemyEventRepository(session)
        self.fingerprints = SQLAlchemyFingerprintRepository(session)
        self.forecasts = SQLAlchemyForecastRepository(session)

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        """Open unit of work scope."""
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Commit on success, rollback on failure."""
        if exc_type is None:
            await self._session.commit()
        else:
            await self._session.rollback()

    async def commit(self) -> None:
        """Commit transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback transaction."""
        await self._session.rollback()
