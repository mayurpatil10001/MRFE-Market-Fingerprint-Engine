"""MongoDB implementation of EventRepository for document workloads."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, cast

from src.domain.entities.event import Event
from src.domain.interfaces import EventRepository, EventSearchFilters, PaginatedResult, Pagination
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


class MongoEventRepository(EventRepository):
    """MongoDB implementation supporting full-text search."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    async def add(self, entity: Event) -> None:
        """Insert event document."""
        await self._collection.insert_one(self._to_document(entity))

    async def get_by_id(self, entity_id: EventId) -> Event | None:
        """Find event by identifier."""
        document = await self._collection.find_one({"event_id": str(entity_id)})
        return self._to_entity(document) if document else None

    async def update(self, entity: Event) -> None:
        """Update event document."""
        await self._collection.update_one(
            {"event_id": str(entity.event_id)},
            {"$set": self._to_document(entity)},
        )

    async def delete(self, entity_id: EventId) -> None:
        """Delete event document."""
        await self._collection.delete_one({"event_id": str(entity_id)})

    async def search(
        self,
        filters: EventSearchFilters,
        pagination: Pagination,
    ) -> PaginatedResult[Event]:
        """Search events using Mongo query operators."""
        mongo_filter: dict[str, Any] = {}
        if filters.event_type is not None:
            mongo_filter["event_type"] = str(filters.event_type)
        if filters.severity is not None:
            mongo_filter["severity"] = str(filters.severity)
        if filters.source is not None:
            mongo_filter["source"] = filters.source
        if filters.is_active is not None:
            mongo_filter["is_active"] = filters.is_active
        if filters.query_text:
            mongo_filter["$text"] = {"$search": filters.query_text}

        total = int(await self._collection.count_documents(mongo_filter))
        cursor = (
            self._collection.find(mongo_filter)
            .sort(filters.sort_by, -1 if filters.sort_order.lower() == "desc" else 1)
            .skip((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        documents = cast(list[Mapping[str, Any]], await cursor.to_list(length=pagination.page_size))
        return PaginatedResult(
            items=[self._to_entity(item) for item in documents],
            page=pagination.page,
            page_size=pagination.page_size,
            total=total,
        )

    @staticmethod
    def _to_document(entity: Event) -> dict[str, Any]:
        """Map entity to document."""
        return {
            "event_id": str(entity.event_id),
            "event_type": str(entity.event_type),
            "severity": str(entity.severity),
            "confidence": entity.confidence.value,
            "title": entity.title,
            "description": entity.description,
            "source": entity.source,
            "detected_at": entity.detected_at,
            "impact_assets": list(entity.impact_assets),
            "market_sector": entity.market_sector,
            "country": entity.country,
            "sentiment_score": entity.sentiment_score,
            "is_active": entity.is_active,
            "resolved_at": entity.resolved_at,
            "version": entity.version,
        }

    @staticmethod
    def _to_entity(document: Mapping[str, Any]) -> Event:
        """Map Mongo document to entity."""
        detected_at = cast(datetime, document["detected_at"])
        if detected_at.tzinfo is None:
            detected_at = detected_at.replace(tzinfo=timezone.utc)
        resolved_raw = cast(datetime | None, document.get("resolved_at"))
        resolved_at = resolved_raw
        if resolved_at is not None and resolved_at.tzinfo is None:
            resolved_at = resolved_at.replace(tzinfo=timezone.utc)
        impact_assets = tuple(str(asset) for asset in cast(list[Any], document.get("impact_assets", [])))
        return Event(
            event_id=EventId.from_string(str(document["event_id"])),
            event_type=EventType.from_string(str(document["event_type"])),
            severity=Severity.from_string(str(document["severity"])),
            confidence=Confidence(float(document["confidence"])),
            title=str(document["title"]),
            description=str(document["description"]),
            source=str(document["source"]),
            detected_at=detected_at,
            impact_assets=impact_assets,
            market_sector=(str(document["market_sector"]) if document.get("market_sector") else None),
            country=(str(document["country"]) if document.get("country") else None),
            sentiment_score=(
                float(document["sentiment_score"])
                if document.get("sentiment_score") is not None
                else None
            ),
            is_active=bool(document["is_active"]),
            resolved_at=resolved_at,
            version=int(document.get("version", 1)),
        )
