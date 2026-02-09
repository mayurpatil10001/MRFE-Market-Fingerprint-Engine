"""Read use cases for events, fingerprints, and forecasts."""

from __future__ import annotations

from src.application.dto.queries import (
    GetEventByIdQuery,
    GetFingerprintQuery,
    GetForecastQuery,
    SearchEventsQuery,
)
from src.application.dto.responses import (
    EventResponseDTO,
    FingerprintResponseDTO,
    ForecastResponseDTO,
    SearchEventsResponseDTO,
)
from src.application.use_cases.mappers import to_event_dto, to_fingerprint_dto, to_forecast_dto
from src.domain.exceptions import (
    EventNotFoundError,
    FingerprintNotFoundError,
    ForecastNotFoundError,
)
from src.domain.interfaces import EventSearchFilters, Pagination, UnitOfWork
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


class GetEventByIdUseCase:
    """Return one event by id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, query: GetEventByIdQuery) -> EventResponseDTO:
        """Execute query."""
        async with self._uow:
            event = await self._uow.events.get_by_id(EventId.from_string(query.event_id))
            if event is None:
                raise EventNotFoundError("event not found")
        return to_event_dto(event)


class SearchEventsUseCase:
    """Search events with pagination and filters."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, query: SearchEventsQuery) -> SearchEventsResponseDTO:
        """Execute query."""
        filters = EventSearchFilters(
            event_type=EventType.from_string(query.event_type) if query.event_type else None,
            severity=Severity.from_string(query.severity) if query.severity else None,
            source=query.source,
            is_active=query.is_active,
            query_text=query.query_text,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )
        pagination = Pagination(page=query.page, page_size=query.page_size)
        async with self._uow:
            result = await self._uow.events.search(filters=filters, pagination=pagination)
        return SearchEventsResponseDTO(
            items=[to_event_dto(item) for item in result.items],
            page=result.page,
            page_size=result.page_size,
            total=result.total,
        )


class GetFingerprintUseCase:
    """Return one fingerprint by id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, query: GetFingerprintQuery) -> FingerprintResponseDTO:
        """Execute query."""
        async with self._uow:
            entity = await self._uow.fingerprints.get_by_id(EventId.from_string(query.fingerprint_id))
            if entity is None:
                raise FingerprintNotFoundError("fingerprint not found")
        return to_fingerprint_dto(entity)


class GetForecastUseCase:
    """Return one forecast by id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    async def execute(self, query: GetForecastQuery) -> ForecastResponseDTO:
        """Execute query."""
        async with self._uow:
            entity = await self._uow.forecasts.get_by_id(EventId.from_string(query.forecast_id))
            if entity is None:
                raise ForecastNotFoundError("forecast not found")
        return to_forecast_dto(entity)
