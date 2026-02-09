"""Unit tests for CQRS use cases."""

from __future__ import annotations

import pytest

from src.application.dto.commands import DetectEventFromNewsCommand
from src.application.use_cases.event_detection_use_case import DetectEventFromNewsUseCase
from src.domain.entities.event import Event
from src.domain.interfaces.event_detection_service import DetectedEventCandidate
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


class FakeDetector:
    """Fake detector for command test."""

    async def detect_from_news(self, news_content: str, source: str) -> list[DetectedEventCandidate]:
        return [
            DetectedEventCandidate(
                event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
                severity=Severity.from_string("HIGH"),
                confidence=0.88,
                title="Detected event",
                description=news_content,
                impact_assets=("AAPL",),
            )
        ]


class FakeEventRepo:
    """In-memory event repository."""

    def __init__(self) -> None:
        self.items: list[Event] = []

    async def add(self, entity: Event) -> None:
        self.items.append(entity)

    async def get_by_id(self, entity_id):  # pragma: no cover - not used
        return None

    async def update(self, entity: Event) -> None:  # pragma: no cover - not used
        return None

    async def delete(self, entity_id) -> None:  # pragma: no cover - not used
        return None

    async def search(self, filters, pagination):  # pragma: no cover - not used
        raise NotImplementedError


class FakeUow:
    """Minimal fake UnitOfWork."""

    def __init__(self) -> None:
        self.events = FakeEventRepo()
        self.fingerprints = object()
        self.forecasts = object()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False


@pytest.mark.asyncio
async def test_detect_event_command_persists_events() -> None:
    """Detect command should create and persist one event."""
    uow = FakeUow()
    use_case = DetectEventFromNewsUseCase(uow=uow, detector=FakeDetector())
    result = await use_case.execute(
        DetectEventFromNewsCommand(
            news_content="Company announced earnings and shares rallied strongly.",
            source="wire",
        )
    )
    assert len(result) == 1
    assert uow.committed is True
    assert len(uow.events.items) == 1
