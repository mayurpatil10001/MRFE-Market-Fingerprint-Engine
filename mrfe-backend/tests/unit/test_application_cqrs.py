"""Expanded application-layer CQRS tests."""

from __future__ import annotations

from typing import Protocol

import pytest

from src.application.dto.base_dto import ResultEnvelope
from src.application.dto.commands import (
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
from src.application.use_cases.fingerprint_generation_use_case import (
    GenerateFingerprintUseCase,
    UpdateFingerprintUseCase,
)
from src.application.use_cases.forecast_generation_use_case import GenerateForecastUseCase
from src.application.use_cases.get_event_by_id_use_case import (
    GetEventByIdUseCase,
    GetFingerprintUseCase,
    GetForecastUseCase,
    SearchEventsUseCase,
)
from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.entities.forecast import Forecast
from src.domain.exceptions import (
    EventNotFoundError,
    FingerprintNotFoundError,
    ForecastNotFoundError,
)
from src.domain.interfaces import FingerprintGenerationResult, ForecastGenerationResult
from src.domain.interfaces.event_repository import PaginatedResult, Pagination
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_id import EventId
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


def _event() -> Event:
    return Event.create(
        event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
        severity=Severity.from_string("MEDIUM"),
        confidence=Confidence(0.8),
        title="Earnings surprise",
        description="Beat and raise",
        source="wire",
        impact_assets=("AAPL",),
    )


def _fingerprint(event_id: EventId) -> Fingerprint:
    return Fingerprint.create(
        event_id=event_id,
        asset_symbol="AAPL",
        reaction_patterns={"impulse": 0.4},
        baseline_metrics={"vol": 0.2},
        reaction_intensity=0.6,
        duration_minutes=60,
        volatility_impact=0.2,
        volume_impact=0.3,
        confidence=Confidence(0.7),
        model_version="v1",
    )


def _forecast(event_id: EventId, fingerprint_id: EventId) -> Forecast:
    return Forecast.create(
        event_id=event_id,
        fingerprint_id=fingerprint_id,
        asset_symbol="AAPL",
        forecast_horizon_hours=12,
        probability_distribution={
            "strong_negative": 0.1,
            "negative": 0.2,
            "neutral": 0.4,
            "positive": 0.2,
            "strong_positive": 0.1,
        },
        predicted_movement=0.2,
        confidence=Confidence(0.71),
        risk_metrics={"model_uncertainty": 0.2},
        model_version="v1",
    )


class InMemoryEventsRepo:
    def __init__(self, items: dict[str, Event] | None = None) -> None:
        self.items = items or {}

    async def add(self, entity: Event) -> None:
        self.items[str(entity.event_id)] = entity

    async def get_by_id(self, entity_id: EventId) -> Event | None:
        return self.items.get(str(entity_id))

    async def update(self, entity: Event) -> None:
        self.items[str(entity.event_id)] = entity

    async def delete(self, entity_id: EventId) -> None:
        self.items.pop(str(entity_id), None)

    async def search(self, filters, pagination: Pagination) -> PaginatedResult[Event]:
        rows = list(self.items.values())
        return PaginatedResult(
            items=rows[: pagination.page_size],
            page=pagination.page,
            page_size=pagination.page_size,
            total=len(rows),
        )


class InMemoryFingerprintsRepo:
    def __init__(self, items: dict[str, Fingerprint] | None = None) -> None:
        self.items = items or {}

    async def add(self, entity: Fingerprint) -> None:
        self.items[str(entity.fingerprint_id)] = entity

    async def get_by_id(self, entity_id: EventId) -> Fingerprint | None:
        return self.items.get(str(entity_id))

    async def update(self, entity: Fingerprint) -> None:
        self.items[str(entity.fingerprint_id)] = entity

    async def delete(self, entity_id: EventId) -> None:
        self.items.pop(str(entity_id), None)

    async def get_by_event_asset(self, event_id: EventId, asset_symbol: str) -> Fingerprint | None:
        for item in self.items.values():
            if str(item.event_id) == str(event_id) and item.asset_symbol == asset_symbol:
                return item
        return None

    async def list_by_event(self, event_id: EventId) -> list[Fingerprint]:
        return [item for item in self.items.values() if str(item.event_id) == str(event_id)]

    async def search_by_asset(self, asset_symbol: str, pagination: Pagination) -> PaginatedResult[Fingerprint]:
        rows = [item for item in self.items.values() if item.asset_symbol == asset_symbol]
        return PaginatedResult(items=rows, page=pagination.page, page_size=pagination.page_size, total=len(rows))


class InMemoryForecastsRepo:
    def __init__(self, items: dict[str, Forecast] | None = None) -> None:
        self.items = items or {}

    async def add(self, entity: Forecast) -> None:
        self.items[str(entity.forecast_id)] = entity

    async def get_by_id(self, entity_id: EventId) -> Forecast | None:
        return self.items.get(str(entity_id))

    async def update(self, entity: Forecast) -> None:
        self.items[str(entity.forecast_id)] = entity

    async def delete(self, entity_id: EventId) -> None:
        self.items.pop(str(entity_id), None)

    async def list_by_event(self, event_id: EventId) -> list[Forecast]:
        return [item for item in self.items.values() if str(item.event_id) == str(event_id)]

    async def get_by_event_asset(self, event_id: EventId, asset_symbol: str) -> Forecast | None:
        for item in self.items.values():
            if str(item.event_id) == str(event_id) and item.asset_symbol == asset_symbol:
                return item
        return None

    async def list_expired(self) -> list[Forecast]:
        return []

    async def search_by_asset(self, asset_symbol: str, pagination: Pagination) -> PaginatedResult[Forecast]:
        rows = [item for item in self.items.values() if item.asset_symbol == asset_symbol]
        return PaginatedResult(items=rows, page=pagination.page, page_size=pagination.page_size, total=len(rows))


class FakeUow:
    def __init__(
        self,
        events: InMemoryEventsRepo,
        fingerprints: InMemoryFingerprintsRepo,
        forecasts: InMemoryForecastsRepo,
    ) -> None:
        self.events = events
        self.fingerprints = fingerprints
        self.forecasts = forecasts
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        return None


class FakeFingerprintGenerator:
    async def generate(self, event: Event, asset_symbol: str, model_version: str) -> FingerprintGenerationResult:
        return FingerprintGenerationResult(
            reaction_patterns={"impulse": 0.3},
            baseline_metrics={"vol": 0.2},
            reaction_intensity=0.5,
            duration_minutes=45,
            volatility_impact=0.2,
            volume_impact=0.3,
            confidence=0.75,
        )


class FakeForecastGenerator:
    async def generate(
        self,
        event: Event,
        fingerprint: Fingerprint,
        asset_symbol: str,
        forecast_horizon_hours: int,
        model_version: str,
    ) -> ForecastGenerationResult:
        return ForecastGenerationResult(
            probability_distribution={
                "strong_negative": 0.1,
                "negative": 0.2,
                "neutral": 0.4,
                "positive": 0.2,
                "strong_positive": 0.1,
            },
            predicted_movement=0.2,
            confidence=0.7,
            risk_metrics={"model_uncertainty": 0.2},
        )


@pytest.mark.asyncio
async def test_fingerprint_usecases_success_and_errors() -> None:
    event = _event()
    events = InMemoryEventsRepo({str(event.event_id): event})
    fingerprints = InMemoryFingerprintsRepo()
    forecasts = InMemoryForecastsRepo()
    uow = FakeUow(events, fingerprints, forecasts)

    generated = await GenerateFingerprintUseCase(uow=uow, generator=FakeFingerprintGenerator()).execute(
        GenerateFingerprintCommand(event_id=str(event.event_id), asset_symbol="AAPL", model_version="v1")
    )
    assert generated.event_id == str(event.event_id)

    updated = await UpdateFingerprintUseCase(uow=uow).execute(
        UpdateFingerprintCommand(
            fingerprint_id=generated.fingerprint_id,
            reaction_intensity=0.9,
            volatility_impact=0.11,
            volume_impact=0.21,
        )
    )
    assert updated.reaction_intensity == 0.9
    assert uow.commits >= 2

    with pytest.raises(EventNotFoundError):
        missing_uow = FakeUow(InMemoryEventsRepo(), InMemoryFingerprintsRepo(), InMemoryForecastsRepo())
        await GenerateFingerprintUseCase(missing_uow, FakeFingerprintGenerator()).execute(
            GenerateFingerprintCommand(
                event_id=str(EventId.new()),
                asset_symbol="AAPL",
                model_version="v1",
            )
        )
    with pytest.raises(FingerprintNotFoundError):
        await UpdateFingerprintUseCase(uow=FakeUow(events, InMemoryFingerprintsRepo(), forecasts)).execute(
            UpdateFingerprintCommand(fingerprint_id=str(EventId.new()))
        )


@pytest.mark.asyncio
async def test_forecast_usecase_success_and_errors() -> None:
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    events = InMemoryEventsRepo({str(event.event_id): event})
    fingerprints = InMemoryFingerprintsRepo({str(fingerprint.fingerprint_id): fingerprint})
    forecasts = InMemoryForecastsRepo()
    uow = FakeUow(events, fingerprints, forecasts)

    forecast_dto = await GenerateForecastUseCase(uow=uow, generator=FakeForecastGenerator()).execute(
        GenerateForecastCommand(
            event_id=str(event.event_id),
            fingerprint_id=str(fingerprint.fingerprint_id),
            asset_symbol="AAPL",
            forecast_horizon_hours=12,
            model_version="v1",
        )
    )
    assert forecast_dto.event_id == str(event.event_id)

    with pytest.raises(EventNotFoundError):
        await GenerateForecastUseCase(
            uow=FakeUow(InMemoryEventsRepo(), fingerprints, forecasts),
            generator=FakeForecastGenerator(),
        ).execute(
            GenerateForecastCommand(
                event_id=str(EventId.new()),
                fingerprint_id=str(fingerprint.fingerprint_id),
                asset_symbol="AAPL",
                forecast_horizon_hours=12,
                model_version="v1",
            )
        )
    with pytest.raises(FingerprintNotFoundError):
        await GenerateForecastUseCase(
            uow=FakeUow(events, InMemoryFingerprintsRepo(), forecasts),
            generator=FakeForecastGenerator(),
        ).execute(
            GenerateForecastCommand(
                event_id=str(event.event_id),
                fingerprint_id=str(EventId.new()),
                asset_symbol="AAPL",
                forecast_horizon_hours=12,
                model_version="v1",
            )
        )


@pytest.mark.asyncio
async def test_query_usecases_and_result_envelope() -> None:
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    forecast = _forecast(event.event_id, fingerprint.fingerprint_id)
    events = InMemoryEventsRepo({str(event.event_id): event})
    fingerprints = InMemoryFingerprintsRepo({str(fingerprint.fingerprint_id): fingerprint})
    forecasts = InMemoryForecastsRepo({str(forecast.forecast_id): forecast})
    uow = FakeUow(events, fingerprints, forecasts)

    event_dto = await GetEventByIdUseCase(uow=uow).execute(GetEventByIdQuery(event_id=str(event.event_id)))
    assert event_dto.event_id == str(event.event_id)
    list_dto = await SearchEventsUseCase(uow=uow).execute(
        SearchEventsQuery(event_type="EARNINGS_ANNOUNCEMENT", severity="MEDIUM")
    )
    assert list_dto.total == 1
    fp_dto = await GetFingerprintUseCase(uow=uow).execute(
        GetFingerprintQuery(fingerprint_id=str(fingerprint.fingerprint_id))
    )
    fc_dto = await GetForecastUseCase(uow=uow).execute(
        GetForecastQuery(forecast_id=str(forecast.forecast_id))
    )
    assert fp_dto.fingerprint_id == str(fingerprint.fingerprint_id)
    assert fc_dto.forecast_id == str(forecast.forecast_id)

    with pytest.raises(EventNotFoundError):
        await GetEventByIdUseCase(FakeUow(InMemoryEventsRepo(), fingerprints, forecasts)).execute(
            GetEventByIdQuery(event_id=str(EventId.new()))
        )
    with pytest.raises(FingerprintNotFoundError):
        await GetFingerprintUseCase(FakeUow(events, InMemoryFingerprintsRepo(), forecasts)).execute(
            GetFingerprintQuery(fingerprint_id=str(EventId.new()))
        )
    with pytest.raises(ForecastNotFoundError):
        await GetForecastUseCase(FakeUow(events, fingerprints, InMemoryForecastsRepo())).execute(
            GetForecastQuery(forecast_id=str(EventId.new()))
        )

    ok_result = ResultEnvelope[str].ok("x")
    fail_result = ResultEnvelope[str].fail("ERR", "bad")
    assert ok_result.success is True
    assert fail_result.success is False


def test_application_interfaces_protocol_imported() -> None:
    from src.application.interfaces import CommandHandler, QueryHandler

    class _CommandHandler(CommandHandler[str, str], Protocol):
        ...

    class _QueryHandler(QueryHandler[str, str], Protocol):
        ...

    assert _CommandHandler is not None
    assert _QueryHandler is not None
