"""Seed demo data."""

from __future__ import annotations

import asyncio

from src.domain.entities.event import Event
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.database.models import Base
from src.infrastructure.database.repositories.event_repository_impl import SQLAlchemyEventRepository
from src.infrastructure.database.session import session_manager


async def seed() -> None:
    """Seed one demo event."""
    session_manager.init()
    async with session_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with session_manager.session() as session:
        repo = SQLAlchemyEventRepository(session)
        event = Event.create(
            event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
            severity=Severity.from_string("MEDIUM"),
            confidence=Confidence(0.72),
            title="Demo event",
            description="Seeded event for local environment",
            source="seed",
            impact_assets=("SPY",),
        )
        await repo.add(event)
        await session.commit()
    await session_manager.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
