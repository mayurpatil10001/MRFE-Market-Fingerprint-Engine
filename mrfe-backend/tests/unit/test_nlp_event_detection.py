"""Unit tests for NLP-augmented event detection service."""

from __future__ import annotations

import pytest

from src.infrastructure.ml.nlp_event_detection_service import NLPAugmentedEventDetectionService


@pytest.mark.asyncio
async def test_nlp_service_matches_taxonomy_rule() -> None:
    service = NLPAugmentedEventDetectionService()
    results = await service.detect_from_news(
        news_content="Fed officials signaled a potential rate cut as inflation cools.",
        source="wire",
    )
    assert results
    top = results[0]
    assert str(top.event_type) == "MACRO_ECONOMIC"
    assert top.confidence >= 0.5


@pytest.mark.asyncio
async def test_nlp_service_falls_back_when_no_taxonomy_match() -> None:
    service = NLPAugmentedEventDetectionService()
    results = await service.detect_from_news(
        news_content="Company introduced a new cloud initiative with regional hiring plans.",
        source="wire",
    )
    assert results
