"""Repository contracts for fingerprints."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.domain.entities.fingerprint import Fingerprint
from src.domain.interfaces.event_repository import AbstractRepository, PaginatedResult, Pagination
from src.domain.value_objects.event_id import EventId


class FingerprintRepository(AbstractRepository[Fingerprint, EventId], ABC):
    """Fingerprint repository API."""

    @abstractmethod
    async def get_by_id(self, entity_id: EventId) -> Optional[Fingerprint]:
        """Fetch fingerprint by id."""

    @abstractmethod
    async def get_by_event_asset(self, event_id: EventId, asset_symbol: str) -> Optional[Fingerprint]:
        """Fetch fingerprint by event and asset."""

    @abstractmethod
    async def list_by_event(self, event_id: EventId) -> Sequence[Fingerprint]:
        """Return fingerprints for one event."""

    @abstractmethod
    async def search_by_asset(
        self,
        asset_symbol: str,
        pagination: Pagination,
    ) -> PaginatedResult[Fingerprint]:
        """Search fingerprints by asset symbol."""
