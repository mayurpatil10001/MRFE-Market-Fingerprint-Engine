"""Tests for MRFEApplicationService method dispatch."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.application.dto.commands import GenerateFingerprintCommand, GenerateForecastCommand
from src.application.dto.queries import (
    GetEventByIdQuery,
    GetFingerprintQuery,
    GetForecastQuery,
    SearchEventsQuery,
)
from src.application.services.mrfe_application_service import MRFEApplicationService


@dataclass
class _ExecStub:
    result: object

    async def execute(self, payload: object) -> object:
        return self.result


@pytest.mark.asyncio
async def test_application_service_dispatches_all_handlers() -> None:
    service = MRFEApplicationService(
        detect_event_from_news=_ExecStub(result=["event"]),  # type: ignore[arg-type]
        generate_fingerprint=_ExecStub(result="fp"),  # type: ignore[arg-type]
        update_fingerprint=_ExecStub(result="fp2"),  # type: ignore[arg-type]
        generate_forecast=_ExecStub(result="fc"),  # type: ignore[arg-type]
        get_event_by_id=_ExecStub(result="e"),  # type: ignore[arg-type]
        search_events=_ExecStub(result="s"),  # type: ignore[arg-type]
        get_fingerprint=_ExecStub(result="gf"),  # type: ignore[arg-type]
        get_forecast=_ExecStub(result="gc"),  # type: ignore[arg-type]
    )
    assert await service.handle_generate_fingerprint(
        GenerateFingerprintCommand(event_id="00000000-0000-0000-0000-000000000000", asset_symbol="AAPL")
    ) == "fp"
    assert await service.handle_generate_forecast(
        GenerateForecastCommand(
            event_id="00000000-0000-0000-0000-000000000000",
            fingerprint_id="00000000-0000-0000-0000-000000000001",
            asset_symbol="AAPL",
        )
    ) == "fc"
    assert await service.handle_get_event(
        GetEventByIdQuery(event_id="00000000-0000-0000-0000-000000000000")
    ) == "e"
    assert await service.handle_search_events(SearchEventsQuery()) == "s"
    assert await service.handle_get_fingerprint(
        GetFingerprintQuery(fingerprint_id="00000000-0000-0000-0000-000000000000")
    ) == "gf"
    assert await service.handle_get_forecast(
        GetForecastQuery(forecast_id="00000000-0000-0000-0000-000000000000")
    ) == "gc"
