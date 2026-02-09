"""SQLAlchemy implementation of EventRepository."""

from __future__ import annotations

from datetime import timezone

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.event import Event
from src.domain.interfaces import EventRepository, EventSearchFilters, PaginatedResult, Pagination
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.database.models.event_model import EventModel
from src.infrastructure.database.repositories.base_repository import SQLAlchemyRepository


class SQLAlchemyEventRepository(SQLAlchemyRepository[EventModel], EventRepository):
    """Event repository backed by PostgreSQL/SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add(self, entity: Event) -> None:
        """Insert event row."""
        self.session.add(self._to_model(entity))

    async def get_by_id(self, entity_id: EventId) -> Event | None:
        """Fetch event by id."""
        stmt = select(EventModel).where(EventModel.event_id == str(entity_id))
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(record) if record else None

    async def update(self, entity: Event) -> None:
        """Update event row with optimistic lock check."""
        stmt = select(EventModel).where(EventModel.event_id == str(entity.event_id))
        record = (await self.session.execute(stmt)).scalar_one()
        record.event_type = str(entity.event_type)
        record.severity = str(entity.severity)
        record.confidence = entity.confidence.value
        record.title = entity.title
        record.description = entity.description
        record.source = entity.source
        record.detected_at = entity.detected_at
        record.impact_assets = list(entity.impact_assets)
        record.market_sector = entity.market_sector
        record.country = entity.country
        record.sentiment_score = entity.sentiment_score
        record.is_active = entity.is_active
        record.resolved_at = entity.resolved_at
        record.version = entity.version

    async def delete(self, entity_id: EventId) -> None:
        """Delete event row."""
        stmt = select(EventModel).where(EventModel.event_id == str(entity_id))
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        if record is not None:
            await self.session.delete(record)

    async def search(
        self,
        filters: EventSearchFilters,
        pagination: Pagination,
    ) -> PaginatedResult[Event]:
        """Search events with filters."""
        stmt = select(EventModel)
        count_stmt = select(func.count(EventModel.id))
        if filters.event_type:
            stmt = stmt.where(EventModel.event_type == str(filters.event_type))
            count_stmt = count_stmt.where(EventModel.event_type == str(filters.event_type))
        if filters.severity:
            stmt = stmt.where(EventModel.severity == str(filters.severity))
            count_stmt = count_stmt.where(EventModel.severity == str(filters.severity))
        if filters.source:
            stmt = stmt.where(EventModel.source == filters.source)
            count_stmt = count_stmt.where(EventModel.source == filters.source)
        if filters.is_active is not None:
            stmt = stmt.where(EventModel.is_active == filters.is_active)
            count_stmt = count_stmt.where(EventModel.is_active == filters.is_active)
        if filters.query_text:
            like = f"%{filters.query_text}%"
            stmt = stmt.where(EventModel.title.ilike(like) | EventModel.description.ilike(like))
            count_stmt = count_stmt.where(EventModel.title.ilike(like) | EventModel.description.ilike(like))
        order_column = EventModel.detected_at if filters.sort_by == "detected_at" else EventModel.created_at
        ordering = desc(order_column) if filters.sort_order.lower() == "desc" else asc(order_column)
        stmt = stmt.order_by(ordering)
        stmt = stmt.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size)

        total = int((await self.session.execute(count_stmt)).scalar_one())
        items = (await self.session.execute(stmt)).scalars().all()
        return PaginatedResult(
            items=[self._to_entity(item) for item in items],
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    def _to_model(self, entity: Event) -> EventModel:
        """Map Event entity to SQLAlchemy model."""
        return EventModel(
            event_id=str(entity.event_id),
            event_type=str(entity.event_type),
            severity=str(entity.severity),
            confidence=entity.confidence.value,
            title=entity.title,
            description=entity.description,
            source=entity.source,
            detected_at=entity.detected_at,
            impact_assets=list(entity.impact_assets),
            market_sector=entity.market_sector,
            country=entity.country,
            sentiment_score=entity.sentiment_score,
            is_active=entity.is_active,
            resolved_at=entity.resolved_at,
            version=entity.version,
        )

    def _to_entity(self, record: EventModel) -> Event:
        """Map SQLAlchemy model to Event entity."""
        detected_at = record.detected_at
        if detected_at.tzinfo is None:
            detected_at = detected_at.replace(tzinfo=timezone.utc)
        resolved_at = record.resolved_at
        if resolved_at is not None and resolved_at.tzinfo is None:
            resolved_at = resolved_at.replace(tzinfo=timezone.utc)
        return Event(
            event_id=EventId.from_string(record.event_id),
            event_type=EventType.from_string(record.event_type),
            severity=Severity.from_string(record.severity),
            confidence=Confidence(record.confidence),
            title=record.title,
            description=record.description,
            source=record.source,
            detected_at=detected_at,
            impact_assets=tuple(record.impact_assets),
            market_sector=record.market_sector,
            country=record.country,
            sentiment_score=record.sentiment_score,
            is_active=record.is_active,
            resolved_at=resolved_at,
            version=record.version,
        )
