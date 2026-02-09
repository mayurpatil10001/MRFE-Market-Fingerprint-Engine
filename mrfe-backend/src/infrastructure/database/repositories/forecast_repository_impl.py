"""SQLAlchemy implementation of ForecastRepository."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.forecast import Forecast
from src.domain.interfaces import ForecastRepository, PaginatedResult, Pagination
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.infrastructure.database.models.forecast_model import ForecastModel
from src.infrastructure.database.repositories.base_repository import SQLAlchemyRepository


class SQLAlchemyForecastRepository(SQLAlchemyRepository[ForecastModel], ForecastRepository):
    """Forecast repository backed by SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add(self, entity: Forecast) -> None:
        """Insert forecast row."""
        self.session.add(self._to_model(entity))

    async def get_by_id(self, entity_id: EventId) -> Forecast | None:
        """Fetch forecast by id."""
        stmt = select(ForecastModel).where(ForecastModel.forecast_id == str(entity_id))
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(record) if record else None

    async def update(self, entity: Forecast) -> None:
        """Update forecast row."""
        stmt = select(ForecastModel).where(ForecastModel.forecast_id == str(entity.forecast_id))
        record = (await self.session.execute(stmt)).scalar_one()
        record.probability_distribution = entity.probability_distribution
        record.predicted_movement = entity.predicted_movement
        record.confidence = entity.confidence.value
        record.risk_metrics = entity.risk_metrics
        record.expires_at = entity.expires_at
        record.version = entity.version

    async def delete(self, entity_id: EventId) -> None:
        """Delete forecast row."""
        stmt = select(ForecastModel).where(ForecastModel.forecast_id == str(entity_id))
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        if record is not None:
            await self.session.delete(record)

    async def list_by_event(self, event_id: EventId) -> list[Forecast]:
        """List forecasts for event."""
        stmt = select(ForecastModel).where(ForecastModel.event_id == str(event_id))
        records = (await self.session.execute(stmt)).scalars().all()
        return [self._to_entity(item) for item in records]

    async def get_by_event_asset(self, event_id: EventId, asset_symbol: str) -> Forecast | None:
        """Fetch forecast by event and asset symbol."""
        stmt = select(ForecastModel).where(
            ForecastModel.event_id == str(event_id),
            ForecastModel.asset_symbol == asset_symbol.upper(),
        )
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(record) if record else None

    async def list_expired(self) -> list[Forecast]:
        """Return expired forecasts."""
        stmt = select(ForecastModel).where(ForecastModel.expires_at < datetime.now(tz=timezone.utc))
        records = (await self.session.execute(stmt)).scalars().all()
        return [self._to_entity(item) for item in records]

    async def search_by_asset(
        self,
        asset_symbol: str,
        pagination: Pagination,
    ) -> PaginatedResult[Forecast]:
        """Search forecasts by asset."""
        normalized = asset_symbol.upper()
        count_stmt = select(func.count(ForecastModel.id)).where(ForecastModel.asset_symbol == normalized)
        stmt = (
            select(ForecastModel)
            .where(ForecastModel.asset_symbol == normalized)
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        total = int((await self.session.execute(count_stmt)).scalar_one())
        records = (await self.session.execute(stmt)).scalars().all()
        return PaginatedResult(
            items=[self._to_entity(item) for item in records],
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    def _to_model(self, entity: Forecast) -> ForecastModel:
        """Map entity to model."""
        return ForecastModel(
            forecast_id=str(entity.forecast_id),
            event_id=str(entity.event_id),
            fingerprint_id=str(entity.fingerprint_id),
            asset_symbol=entity.asset_symbol,
            forecast_horizon_hours=entity.forecast_horizon_hours,
            probability_distribution=entity.probability_distribution,
            predicted_movement=entity.predicted_movement,
            confidence=entity.confidence.value,
            risk_metrics=entity.risk_metrics,
            model_version=entity.model_version,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
            version=entity.version,
        )

    def _to_entity(self, record: ForecastModel) -> Forecast:
        """Map model to entity."""
        created_at = record.created_at
        expires_at = record.expires_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return Forecast(
            forecast_id=EventId.from_string(record.forecast_id),
            event_id=EventId.from_string(record.event_id),
            fingerprint_id=EventId.from_string(record.fingerprint_id),
            asset_symbol=record.asset_symbol,
            forecast_horizon_hours=record.forecast_horizon_hours,
            probability_distribution=record.probability_distribution,
            predicted_movement=record.predicted_movement,
            confidence=Confidence(record.confidence),
            risk_metrics=record.risk_metrics,
            model_version=record.model_version,
            created_at=created_at,
            expires_at=expires_at,
            version=record.version,
        )
