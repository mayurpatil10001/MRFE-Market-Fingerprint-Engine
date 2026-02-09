"""Use case for DetectEventFromNewsCommand."""

from __future__ import annotations

from src.application.dto.commands import DetectEventFromNewsCommand
from src.application.dto.responses import EventResponseDTO
from src.application.use_cases.mappers import to_event_dto
from src.domain.entities.factories.event_factory import EventFactory
from src.domain.interfaces import EventDetectionService, UnitOfWork
from src.domain.value_objects.confidence import Confidence


class DetectEventFromNewsUseCase:
    """Detect market events from unstructured news text."""

    def __init__(self, uow: UnitOfWork, detector: EventDetectionService) -> None:
        self._uow = uow
        self._detector = detector

    async def execute(self, command: DetectEventFromNewsCommand) -> list[EventResponseDTO]:
        """Execute command in one transaction boundary."""
        async with self._uow:
            candidates = await self._detector.detect_from_news(
                news_content=command.news_content,
                source=command.source,
            )
            events: list[EventResponseDTO] = []
            for candidate in candidates:
                event = EventFactory.create(
                    event_type=candidate.event_type,
                    severity=candidate.severity,
                    confidence=Confidence(candidate.confidence),
                    title=candidate.title,
                    description=candidate.description,
                    source=command.source,
                    impact_assets=candidate.impact_assets,
                    market_sector=candidate.market_sector,
                    country=candidate.country,
                    sentiment_score=candidate.sentiment_score,
                )
                await self._uow.events.add(event)
                events.append(to_event_dto(event))
            await self._uow.commit()
        return events
