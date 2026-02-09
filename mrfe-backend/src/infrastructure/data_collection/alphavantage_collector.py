"""AlphaVantage news collector utilities."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from src.core.config.settings import settings
from src.core.logging import get_logger
from src.infrastructure.data_collection.newsapi_collector import NewsAPIArticle

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AlphaVantageArticle:
    """Normalized AlphaVantage article payload."""

    article_id: str
    source: str
    title: str
    summary: str
    url: str
    published_at: datetime
    author: str | None = None


class AlphaVantageNewsCollector:
    """Collect news entries from AlphaVantage's NEWS_SENTIMENT endpoint."""

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 20.0) -> None:
        self._api_key = api_key or settings.alphavantage_api_key
        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            base_url=settings.alphavantage_base_url.rstrip("/"),
        )

    async def fetch_news(
        self,
        query: str | None = None,
        limit: int = 50,
    ) -> list[NewsAPIArticle]:
        """Fetch latest news feed and normalize into shared article schema."""
        if not self._api_key:
            return []
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self._api_key,
            "sort": "LATEST",
            "limit": min(max(limit, 1), 200),
        }
        if query:
            params["topics"] = query
            params["tickers"] = query
        response = await self._client.get("", params=params)
        response.raise_for_status()
        payload = response.json()
        feed = payload.get("feed", [])
        if not isinstance(feed, list):
            logger.warning("alphavantage_invalid_feed")
            return []
        return self._parse_feed(feed)

    def _parse_feed(self, feed: list[dict[str, Any]]) -> list[NewsAPIArticle]:
        normalized: list[NewsAPIArticle] = []
        for item in feed:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "") or "").strip()
            if not title:
                continue
            summary = str(item.get("summary", "") or item.get("overview", "") or "").strip()
            url = str(item.get("url", "") or item.get("link", "") or "").strip()
            source = str(item.get("source", "alphavantage")).strip() or "alphavantage"
            published_at = self._parse_date(str(item.get("time_published", "") or ""))
            article_id = self._article_id(source, url or title)
            normalized.append(
                NewsAPIArticle(
                    article_id=article_id,
                    source=source,
                    title=title[:255],
                    summary=summary[:2000],
                    url=url,
                    published_at=published_at,
                    author=None,
                )
            )
        return normalized

    @staticmethod
    def _article_id(source: str, stable_value: str) -> str:
        digest = hashlib.sha256(f"{source}:{stable_value}".encode()).hexdigest()
        return digest[:32]

    @staticmethod
    def _parse_date(raw: str) -> datetime:
        if not raw:
            return datetime.now(tz=UTC)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            try:
                parsed = datetime.strptime(raw, "%Y%m%dT%H%M%S")
                return parsed.replace(tzinfo=UTC)
            except ValueError:
                return datetime.now(tz=UTC)

    async def close(self) -> None:
        """Close HTTP resources."""
        await self._client.aclose()
