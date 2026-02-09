"""Event detection strategy implementations."""

from __future__ import annotations

import re
from collections.abc import Sequence

from src.domain.interfaces import DetectedEventCandidate, EventDetectionService
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity


class RuleBasedEventDetectionService(EventDetectionService):
    """Keyword/rule-based detector used as default strategy."""

    _rules: dict[str, tuple[str, str]] = {
        "earnings": ("EARNINGS_ANNOUNCEMENT", "MEDIUM"),
        "acquisition": ("MERGER_ACQUISITION", "HIGH"),
        "merger": ("MERGER_ACQUISITION", "HIGH"),
        "regulation": ("REGULATORY_CHANGE", "HIGH"),
        "breach": ("TECHNICAL_BREACH", "CRITICAL"),
        "lawsuit": ("LEGAL_ISSUE", "HIGH"),
    }

    async def detect_from_news(
        self,
        news_content: str,
        source: str,
    ) -> Sequence[DetectedEventCandidate]:
        """Detect candidate events from raw text."""
        lowered = news_content.lower()
        assets = tuple({symbol.upper() for symbol in re.findall(r"\$?([A-Z]{2,5})\b", news_content)})
        for keyword, (event_type, severity) in self._rules.items():
            if keyword in lowered:
                title = news_content.strip().split(".")[0][:120]
                return [
                    DetectedEventCandidate(
                        event_type=EventType.from_string(event_type),
                        severity=Severity.from_string(severity),
                        confidence=0.78,
                        title=title or f"{event_type} from {source}",
                        description=news_content.strip(),
                        impact_assets=assets or ("SPY",),
                        sentiment_score=0.1,
                    )
                ]
        return [
            DetectedEventCandidate(
                event_type=EventType.from_string("MACRO_ECONOMIC"),
                severity=Severity.from_string("LOW"),
                confidence=0.52,
                title=news_content.strip().split(".")[0][:120] or f"General news from {source}",
                description=news_content.strip(),
                impact_assets=assets or ("SPY",),
                sentiment_score=0.0,
            )
        ]
