"""Repository contracts and query objects for events."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generic, Optional, Sequence, TypeVar

from src.domain.entities.event import Event
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity

TEntity = TypeVar("TEntity")
TId = TypeVar("TId")


@dataclass(frozen=True, slots=True)
class Pagination:
    """Cursor-less pagination request."""

    page: int = 1
    page_size: int = 50


@dataclass(frozen=True, slots=True)
class PaginatedResult(Generic[TEntity]):
    """Paginated query response."""

    items: Sequence[TEntity]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True, slots=True)
class EventSearchFilters:
    """Filter/sort model for event search."""

    event_type: Optional[EventType] = None
    severity: Optional[Severity] = None
    source: Optional[str] = None
    is_active: Optional[bool] = None
    query_text: Optional[str] = None
    detected_after: Optional[datetime] = None
    detected_before: Optional[datetime] = None
    sort_by: str = "detected_at"
    sort_order: str = "desc"


class AbstractRepository(ABC, Generic[TEntity, TId]):
    """Generic repository abstraction."""

    @abstractmethod
    async def add(self, entity: TEntity) -> None:
        """Persist new entity."""

    @abstractmethod
    async def get_by_id(self, entity_id: TId) -> Optional[TEntity]:
        """Fetch entity by id."""

    @abstractmethod
    async def update(self, entity: TEntity) -> None:
        """Persist entity update."""

    @abstractmethod
    async def delete(self, entity_id: TId) -> None:
        """Delete entity by id."""


class EventRepository(AbstractRepository[Event, EventId], ABC):
    """Event repository API."""

    async def get_by_id(self, entity_id: EventId) -> Optional[Event]:
        """Fetch event by id."""

    @abstractmethod
    async def search(
        self,
        filters: EventSearchFilters,
        pagination: Pagination,
    ) -> PaginatedResult[Event]:
        """Search events with filtering and pagination."""
