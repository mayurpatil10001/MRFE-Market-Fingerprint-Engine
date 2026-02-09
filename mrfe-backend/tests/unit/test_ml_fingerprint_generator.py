"""Unit tests for ML fingerprint generator."""

from __future__ import annotations

import pytest

from src.core.config.settings import settings
from src.domain.entities.event import Event
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.ml.fingerprint_generator_impl import MLFingerprintGenerator


def _event() -> Event:
    return Event.create(
        event_type=EventType.from_string("MERGER_ACQUISITION"),
        severity=Severity.from_string("HIGH"),
        confidence=Confidence(0.82),
        title="Merger announcement",
        description="Company announced a strategic acquisition.",
        source="wire",
        impact_assets=("MSFT",),
        sentiment_score=0.2,
    )


@pytest.mark.asyncio
async def test_ml_fingerprint_generator_fallback(monkeypatch) -> None:
    original_path = settings.fingerprint_regressor_path
    settings.fingerprint_regressor_path = "storage/missing_model.pkl"
    generator = MLFingerprintGenerator()
    result = await generator.generate(event=_event(), asset_symbol="MSFT", model_version="v1")
    settings.fingerprint_regressor_path = original_path
    assert 0.0 <= result.reaction_intensity <= 1.0
