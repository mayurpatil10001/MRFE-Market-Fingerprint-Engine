"""Application facade coordinating CQRS use cases."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.dto.commands import (
    DetectEventFromNewsCommand,
    GenerateFingerprintCommand,
    GenerateForecastCommand,
    UpdateFingerprintCommand,
)
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
from src.application.use_cases import (
    DetectEventFromNewsUseCase,
    GenerateFingerprintUseCase,
    GenerateForecastUseCase,
    GetEventByIdUseCase,
    GetFingerprintUseCase,
    GetForecastUseCase,
    SearchEventsUseCase,
    UpdateFingerprintUseCase,
)


@dataclass(slots=True)
class MRFEApplicationService:
    """High-level facade for API adapters."""

    detect_event_from_news: DetectEventFromNewsUseCase
    generate_fingerprint: GenerateFingerprintUseCase
    update_fingerprint: UpdateFingerprintUseCase
    generate_forecast: GenerateForecastUseCase
    get_event_by_id: GetEventByIdUseCase
    search_events: SearchEventsUseCase
    get_fingerprint: GetFingerprintUseCase
    get_forecast: GetForecastUseCase

    async def handle_detect(self, command: DetectEventFromNewsCommand) -> list[EventResponseDTO]:
        """Dispatch detect command."""
        return await self.detect_event_from_news.execute(command)

    async def handle_generate_fingerprint(
        self,
        command: GenerateFingerprintCommand,
    ) -> FingerprintResponseDTO:
        """Dispatch fingerprint generation command."""
        return await self.generate_fingerprint.execute(command)

    async def handle_update_fingerprint(self, command: UpdateFingerprintCommand) -> FingerprintResponseDTO:
        """Dispatch fingerprint update command."""
        return await self.update_fingerprint.execute(command)

    async def handle_generate_forecast(self, command: GenerateForecastCommand) -> ForecastResponseDTO:
        """Dispatch forecast generation command."""
        return await self.generate_forecast.execute(command)

    async def handle_get_event(self, query: GetEventByIdQuery) -> EventResponseDTO:
        """Dispatch event query."""
        return await self.get_event_by_id.execute(query)

    async def handle_search_events(self, query: SearchEventsQuery) -> SearchEventsResponseDTO:
        """Dispatch event search query."""
        return await self.search_events.execute(query)

    async def handle_get_fingerprint(self, query: GetFingerprintQuery) -> FingerprintResponseDTO:
        """Dispatch fingerprint query."""
        return await self.get_fingerprint.execute(query)

    async def handle_get_forecast(self, query: GetForecastQuery) -> ForecastResponseDTO:
        """Dispatch forecast query."""
        return await self.get_forecast.execute(query)
