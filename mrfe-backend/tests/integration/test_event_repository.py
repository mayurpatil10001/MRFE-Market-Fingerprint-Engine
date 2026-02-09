"""Integration tests for SQLAlchemy repositories."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.entities.event import Event
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.database.models import Base
from src.infrastructure.database.repositories.event_repository_impl import SQLAlchemyEventRepository


@pytest.mark.asyncio
async def test_event_repository_add_and_get() -> None:
    """Persist and fetch event entity."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        repo = SQLAlchemyEventRepository(session)
        event = Event.create(
            event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
            severity=Severity.from_string("HIGH"),
            confidence=Confidence(0.8),
            title="Q4 earnings beat",
            description="Earnings exceeded expectations",
            source="wire",
            impact_assets=("AAPL",),
        )
        await repo.add(event)
        await session.commit()
        fetched = await repo.get_by_id(event.event_id)
        assert fetched is not None
        assert fetched.title == event.title
    await engine.dispose()
