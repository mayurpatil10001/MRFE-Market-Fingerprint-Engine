"""Port for event detection providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


@dataclass(frozen=True, slots=True)
class DetectedEventCandidate:
    """Structured result from detection service."""

    event_type: EventType
    severity: Severity
    confidence: float
    title: str
    description: str
    impact_assets: tuple[str, ...]
    market_sector: Optional[str] = None
    country: Optional[str] = None
    sentiment_score: Optional[float] = None


class EventDetectionService(Protocol):
    """Domain port for event-detection implementation."""

    async def detect_from_news(self, news_content: str, source: str) -> Sequence[DetectedEventCandidate]:
        """Return detected event candidates."""
