"""NLP-augmented event detection service with graceful fallbacks."""

from __future__ import annotations

import re
import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.config.settings import settings
from src.domain.interfaces import DetectedEventCandidate, EventDetectionService
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.ml.event_detection_service_impl import RuleBasedEventDetectionService
from src.infrastructure.ml.model_loader import TextClassificationResult, get_model_loader


@dataclass(frozen=True, slots=True)
class TaxonomyRule:
    """One taxonomy rule loaded from yaml."""

    keywords: tuple[str, ...]
    event_type: str
    severity: str


class NLPAugmentedEventDetectionService(EventDetectionService):
    """Hybrid detector using taxonomy/NER/sentiment with rule-based fallback."""

    def __init__(self, taxonomy_path: str | None = None) -> None:
        self._fallback = RuleBasedEventDetectionService()
        self._rules = self._load_taxonomy(taxonomy_path)
        self._model_loader = get_model_loader()

    async def detect_from_news(self, news_content: str, source: str) -> list[DetectedEventCandidate]:
        """Detect one or more event candidates from free text."""
        text = news_content.strip()
        lowered = text.lower()
        assets = tuple({symbol.upper() for symbol in re.findall(r"\$?([A-Z]{2,5})\b", text)}) or ("SPY",)
        matched = self._match_taxonomy(lowered)
        sentiment = self._sentiment_score(lowered)
        classifier = await self._transformer_sentiment(text)
        if classifier is not None:
            sentiment = classifier.sentiment
        market_sector = self._extract_sector(lowered)
        country = self._extract_country(lowered)

        if matched is None:
            return list(await self._fallback.detect_from_news(news_content=text, source=source))

        title = text.split(".")[0][:120] or f"{matched.event_type} from {source}"
        confidence = 0.81
        if classifier is not None:
            confidence = min(0.98, max(0.6, 0.75 + classifier.score * 0.2))
        candidate = DetectedEventCandidate(
            event_type=EventType.from_string(matched.event_type),
            severity=Severity.from_string(matched.severity),
            confidence=confidence,
            title=title,
            description=text,
            impact_assets=assets,
            market_sector=market_sector,
            country=country,
            sentiment_score=sentiment,
        )
        return [candidate]

    def _match_taxonomy(self, lowered: str) -> TaxonomyRule | None:
        for rule in self._rules:
            if any(keyword in lowered for keyword in rule.keywords):
                return rule
        return None

    @staticmethod
    def _extract_sector(lowered: str) -> str | None:
        sector_map = {
            "semiconductor": "technology",
            "bank": "financials",
            "oil": "energy",
            "pharma": "healthcare",
            "retail": "consumer",
        }
        for keyword, sector in sector_map.items():
            if keyword in lowered:
                return sector
        return None

    @staticmethod
    def _extract_country(lowered: str) -> str | None:
        countries = ("us", "china", "japan", "uk", "germany", "france", "india")
        for country in countries:
            if f" {country} " in f" {lowered} ":
                return country.upper()
        return None

    @staticmethod
    def _sentiment_score(lowered: str) -> float:
        positive_terms = ("beat", "growth", "strong", "upgrade", "surge", "expand")
        negative_terms = ("miss", "decline", "weak", "downgrade", "risk", "lawsuit")
        positive_hits = sum(lowered.count(item) for item in positive_terms)
        negative_hits = sum(lowered.count(item) for item in negative_terms)
        raw = positive_hits - negative_hits
        if raw == 0:
            return 0.0
        return max(-1.0, min(1.0, raw / 5))

    async def _transformer_sentiment(self, text: str) -> TextClassificationResult | None:
        """Optional transformer-based sentiment classification."""
        if os.getenv("PYTEST_CURRENT_TEST"):
            return None
        if not settings.event_classifier_enabled:
            return None
        model_name = settings.event_classifier_model
        if not model_name:
            return None
        pipeline = await self._model_loader.load_text_classifier(
            model_name=model_name,
            device=settings.event_classifier_device,
            local_files_only=settings.event_classifier_local_files_only,
        )
        if pipeline is None:
            return None
        try:
            result = await asyncio.to_thread(pipeline, text, truncation=True, max_length=512)
        except Exception:  # noqa: BLE001
            return None
        if not result:
            return None
        entry = result[0]
        if not isinstance(entry, dict):
            return None
        label = str(entry.get("label", "")).lower()
        score = float(entry.get("score", 0.0))
        if "positive" in label:
            sentiment = 0.6
        elif "negative" in label:
            sentiment = -0.6
        else:
            sentiment = 0.0
        return TextClassificationResult(label=label, score=score, sentiment=sentiment)

    @staticmethod
    def _default_rules() -> tuple[TaxonomyRule, ...]:
        return (
            TaxonomyRule(
                keywords=("fed", "fomc", "rate hike", "rate cut", "ecb"),
                event_type="MACRO_ECONOMIC",
                severity="HIGH",
            ),
            TaxonomyRule(
                keywords=("earnings", "guidance", "eps", "revenue"),
                event_type="EARNINGS_ANNOUNCEMENT",
                severity="MEDIUM",
            ),
            TaxonomyRule(
                keywords=("acquisition", "merger", "buyback"),
                event_type="MERGER_ACQUISITION",
                severity="HIGH",
            ),
            TaxonomyRule(
                keywords=("sanctions", "war", "tariff", "election"),
                event_type="GEO_POLITICAL",
                severity="HIGH",
            ),
        )

    def _load_taxonomy(self, taxonomy_path: str | None) -> tuple[TaxonomyRule, ...]:
        path = Path(taxonomy_path) if taxonomy_path else Path(__file__).with_name("event_taxonomy.yaml")
        if not path.exists():
            return self._default_rules()
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            return self._default_rules()
        payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw_categories = payload.get("categories", [])
        if not isinstance(raw_categories, list):
            return self._default_rules()
        rules: list[TaxonomyRule] = []
        for item in raw_categories:
            if not isinstance(item, dict):
                continue
            keywords = item.get("keywords", [])
            if not isinstance(keywords, list):
                continue
            event_type = item.get("event_type", "MACRO_ECONOMIC")
            severity = item.get("severity", "MEDIUM")
            rules.append(
                TaxonomyRule(
                    keywords=tuple(str(keyword).lower() for keyword in keywords),
                    event_type=str(event_type),
                    severity=str(severity),
                )
            )
        return tuple(rules) if rules else self._default_rules()
