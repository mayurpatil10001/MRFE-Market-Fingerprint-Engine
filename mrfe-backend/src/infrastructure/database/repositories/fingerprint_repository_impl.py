"""SQLAlchemy implementation of FingerprintRepository."""

from __future__ import annotations

from datetime import timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.fingerprint import Fingerprint
from src.domain.interfaces import FingerprintRepository, PaginatedResult, Pagination
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.infrastructure.database.models.fingerprint_model import FingerprintModel
from src.infrastructure.database.repositories.base_repository import SQLAlchemyRepository


class SQLAlchemyFingerprintRepository(SQLAlchemyRepository[FingerprintModel], FingerprintRepository):
    """Fingerprint repository backed by SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def add(self, entity: Fingerprint) -> None:
        """Insert fingerprint row."""
        self.session.add(self._to_model(entity))

    async def get_by_id(self, entity_id: EventId) -> Fingerprint | None:
        """Fetch fingerprint by id."""
        stmt = select(FingerprintModel).where(FingerprintModel.fingerprint_id == str(entity_id))
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(record) if record else None

    async def update(self, entity: Fingerprint) -> None:
        """Update existing fingerprint row."""
        stmt = select(FingerprintModel).where(FingerprintModel.fingerprint_id == str(entity.fingerprint_id))
        record = (await self.session.execute(stmt)).scalar_one()
        record.reaction_intensity = entity.reaction_intensity
        record.volatility_impact = entity.volatility_impact
        record.volume_impact = entity.volume_impact
        record.reaction_patterns = entity.reaction_patterns
        record.baseline_metrics = entity.baseline_metrics
        record.confidence = entity.confidence.value
        record.updated_at = entity.updated_at
        record.version = entity.version

    async def delete(self, entity_id: EventId) -> None:
        """Delete fingerprint row."""
        stmt = select(FingerprintModel).where(FingerprintModel.fingerprint_id == str(entity_id))
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        if record is not None:
            await self.session.delete(record)

    async def get_by_event_asset(self, event_id: EventId, asset_symbol: str) -> Fingerprint | None:
        """Fetch by event and asset."""
        stmt = select(FingerprintModel).where(
            FingerprintModel.event_id == str(event_id),
            FingerprintModel.asset_symbol == asset_symbol.upper(),
        )
        record = (await self.session.execute(stmt)).scalar_one_or_none()
        return self._to_entity(record) if record else None

    async def list_by_event(self, event_id: EventId) -> list[Fingerprint]:
        """List fingerprints by event."""
        stmt = select(FingerprintModel).where(FingerprintModel.event_id == str(event_id))
        records = (await self.session.execute(stmt)).scalars().all()
        return [self._to_entity(item) for item in records]

    async def search_by_asset(
        self,
        asset_symbol: str,
        pagination: Pagination,
    ) -> PaginatedResult[Fingerprint]:
        """Search fingerprints by asset symbol."""
        normalized = asset_symbol.upper()
        count_stmt = select(func.count(FingerprintModel.id)).where(
            FingerprintModel.asset_symbol == normalized
        )
        stmt = (
            select(FingerprintModel)
            .where(FingerprintModel.asset_symbol == normalized)
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

    def _to_model(self, entity: Fingerprint) -> FingerprintModel:
        """Map entity to model."""
        return FingerprintModel(
            fingerprint_id=str(entity.fingerprint_id),
            event_id=str(entity.event_id),
            asset_symbol=entity.asset_symbol,
            reaction_patterns=entity.reaction_patterns,
            baseline_metrics=entity.baseline_metrics,
            reaction_intensity=entity.reaction_intensity,
            duration_minutes=entity.duration_minutes,
            volatility_impact=entity.volatility_impact,
            volume_impact=entity.volume_impact,
            confidence=entity.confidence.value,
            model_version=entity.model_version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            version=entity.version,
        )

    def _to_entity(self, record: FingerprintModel) -> Fingerprint:
        """Map model to entity."""
        created_at = record.created_at
        updated_at = record.updated_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        return Fingerprint(
            fingerprint_id=EventId.from_string(record.fingerprint_id),
            event_id=EventId.from_string(record.event_id),
            asset_symbol=record.asset_symbol,
            reaction_patterns=record.reaction_patterns,
            baseline_metrics=record.baseline_metrics,
            reaction_intensity=record.reaction_intensity,
            duration_minutes=record.duration_minutes,
            volatility_impact=record.volatility_impact,
            volume_impact=record.volume_impact,
            confidence=Confidence(record.confidence),
            model_version=record.model_version,
            created_at=created_at,
            updated_at=updated_at,
            version=record.version,
        )
