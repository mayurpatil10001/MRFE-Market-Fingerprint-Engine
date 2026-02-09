"""NewsAPI data collector utilities."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from src.core.config.settings import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class NewsAPIArticle:
    """Normalized NewsAPI article payload."""

    article_id: str
    source: str
    title: str
    summary: str
    url: str
    published_at: datetime
    author: str | None = None


class NewsAPICollector:
    """Collect news entries from NewsAPI with normalization."""

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 20.0) -> None:
        self._api_key = api_key or settings.newsapi_api_key
        self._client = httpx.AsyncClient(
            timeout=timeout_seconds,
            base_url=settings.newsapi_base_url,
        )

    async def fetch_top_headlines(
        self,
        query: str,
        sources: str | None = None,
        language: str = "en",
        page_size: int = 50,
    ) -> list[NewsAPIArticle]:
        """Fetch top headlines from NewsAPI."""
        if not self._api_key:
            return []
        params = {
            "q": query,
            "language": language,
            "pageSize": page_size,
            "apiKey": self._api_key,
        }
        if sources:
            params["sources"] = sources
        response = await self._client.get("/top-headlines", params=params)
        response.raise_for_status()
        return self._parse_payload(response.json())

    async def fetch_everything(
        self,
        query: str,
        sources: str | None = None,
        language: str = "en",
        page_size: int = 50,
        from_date: str | None = None,
    ) -> list[NewsAPIArticle]:
        """Fetch full news search results from NewsAPI."""
        if not self._api_key:
            return []
        params = {
            "q": query,
            "language": language,
            "pageSize": page_size,
            "apiKey": self._api_key,
            "sortBy": "publishedAt",
        }
        if sources:
            params["sources"] = sources
        if from_date:
            params["from"] = from_date
        response = await self._client.get("/everything", params=params)
        response.raise_for_status()
        return self._parse_payload(response.json())

    def _parse_payload(self, payload: dict[str, Any]) -> list[NewsAPIArticle]:
        items = payload.get("articles", [])
        if not isinstance(items, list):
            return []
        normalized: list[NewsAPIArticle] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "") or "").strip()
            if not title:
                continue
            summary = str(item.get("description", "") or "").strip()
            url = str(item.get("url", "") or "").strip()
            source = self._source_name(item.get("source"))
            author = str(item.get("author", "") or "").strip() or None
            published_at = self._parse_date(str(item.get("publishedAt", "") or ""))
            article_id = self._article_id(source, url or title)
            normalized.append(
                NewsAPIArticle(
                    article_id=article_id,
                    source=source,
                    title=title[:255],
                    summary=summary[:2000],
                    url=url,
                    published_at=published_at,
                    author=author,
                )
            )
        return normalized

    @staticmethod
    def _source_name(raw_source: Any) -> str:
        if isinstance(raw_source, dict):
            name = raw_source.get("name")
            if isinstance(name, str):
                return name[:120]
        return "newsapi"

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
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            return datetime.now(tz=UTC)

    async def close(self) -> None:
        """Close HTTP resources."""
        await self._client.aclose()
