"""Repository contracts for forecasts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.domain.entities.forecast import Forecast
from src.domain.interfaces.event_repository import AbstractRepository, PaginatedResult, Pagination
from src.domain.value_objects.event_id import EventId


class ForecastRepository(AbstractRepository[Forecast, EventId], ABC):
    """Forecast repository API."""

    @abstractmethod
    async def get_by_id(self, entity_id: EventId) -> Optional[Forecast]:
        """Fetch forecast by id."""

    @abstractmethod
    async def list_by_event(self, event_id: EventId) -> Sequence[Forecast]:
        """Return forecasts for an event."""

    @abstractmethod
    async def get_by_event_asset(self, event_id: EventId, asset_symbol: str) -> Optional[Forecast]:
        """Get forecast by event and asset."""

    @abstractmethod
    async def list_expired(self) -> Sequence[Forecast]:
        """Return expired forecasts."""

    @abstractmethod
    async def search_by_asset(
        self,
        asset_symbol: str,
        pagination: Pagination,
    ) -> PaginatedResult[Forecast]:
        """Search forecasts by asset symbol."""
