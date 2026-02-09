"""Unit tests for similarity service."""

from __future__ import annotations

import pytest

from src.domain.entities.event import Event
from src.domain.entities.fingerprint import Fingerprint
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.ml.similarity_service import FingerprintSimilarityService


def _event() -> Event:
    return Event.create(
        event_type=EventType.from_string("EARNINGS_ANNOUNCEMENT"),
        severity=Severity.from_string("MEDIUM"),
        confidence=Confidence(0.76),
        title="Earnings update",
        description="Revenue growth exceeded expectations.",
        source="wire",
        impact_assets=("AAPL",),
        market_sector="technology",
        sentiment_score=0.4,
    )


def _fingerprint(event_id) -> Fingerprint:
    return Fingerprint.create(
        event_id=event_id,
        asset_symbol="AAPL",
        reaction_patterns={"shock": 0.4},
        baseline_metrics={"vol": 0.2},
        reaction_intensity=0.5,
        duration_minutes=120,
        volatility_impact=0.3,
        volume_impact=0.4,
        confidence=Confidence(0.7),
        model_version="v1",
    )


@pytest.mark.asyncio
async def test_similarity_service_records_and_matches(tmp_path) -> None:
    service = FingerprintSimilarityService(store_path=str(tmp_path / "vectors.json"))
    event = _event()
    fingerprint = _fingerprint(event.event_id)
    await service.record(event=event, fingerprint=fingerprint, horizon_hours=24)
    matches = await service.match(event=event, fingerprint=fingerprint, horizon_hours=24, asset_symbol="AAPL")
    assert matches
