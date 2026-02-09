"""News collection pipeline utilities."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

import httpx

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class NewsArticle:
    """Normalized news article payload."""

    article_id: str
    source: str
    title: str
    summary: str
    url: str
    published_at: datetime
    author: str | None = None


class NewsCollector:
    """Collect news entries from RSS feeds with de-duplication."""

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def fetch_rss(self, source_name: str, feed_url: str) -> list[NewsArticle]:
        """Fetch and normalize one RSS feed."""
        response = await self._client.get(feed_url)
        response.raise_for_status()
        return self._parse_rss(source_name=source_name, xml_payload=response.text)

    def deduplicate(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """De-duplicate by stable article_id while preserving order."""
        seen: set[str] = set()
        unique: list[NewsArticle] = []
        for article in articles:
            if article.article_id in seen:
                continue
            seen.add(article.article_id)
            unique.append(article)
        return unique

    def to_mongo_documents(self, articles: list[NewsArticle]) -> list[dict[str, Any]]:
        """Map normalized articles to Mongo-friendly documents."""
        return [
            {
                "_id": article.article_id,
                "source": article.source,
                "title": article.title,
                "summary": article.summary,
                "url": article.url,
                "published_at": article.published_at,
                "author": article.author,
            }
            for article in articles
        ]

    def _parse_rss(self, source_name: str, xml_payload: str) -> list[NewsArticle]:
        """Parse RSS XML into normalized articles."""
        parsed = ElementTree.fromstring(xml_payload)
        items = parsed.findall(".//item")
        articles: list[NewsArticle] = []
        for item in items:
            title = self._text(item, "title")
            if not title:
                continue
            summary = self._clean_html(self._text(item, "description"))
            link = self._text(item, "link")
            guid = self._text(item, "guid")
            pub_date = self._text(item, "pubDate")
            author = self._text(item, "author")
            published_at = self._parse_date(pub_date)
            article_id = self._article_id(source_name, guid or link or title)
            articles.append(
                NewsArticle(
                    article_id=article_id,
                    source=source_name,
                    title=title[:255],
                    summary=summary[:2000],
                    url=link,
                    published_at=published_at,
                    author=author or None,
                )
            )
        return articles

    @staticmethod
    def _text(item: ElementTree.Element, tag: str) -> str:
        node = item.find(tag)
        return node.text.strip() if node is not None and node.text else ""

    @staticmethod
    def _clean_html(value: str) -> str:
        return re.sub(r"<[^>]+>", " ", value).strip()

    @staticmethod
    def _article_id(source_name: str, stable_value: str) -> str:
        digest = hashlib.sha256(f"{source_name}:{stable_value}".encode()).hexdigest()
        return digest[:32]

    @staticmethod
    def _parse_date(raw: str) -> datetime:
        if not raw:
            return datetime.now(tz=UTC)
        try:
            parsed = parsedate_to_datetime(raw)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except (ValueError, TypeError):
            return datetime.now(tz=UTC)

    async def close(self) -> None:
        """Close HTTP resources."""
        await self._client.aclose()
