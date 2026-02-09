"""News ingestion endpoints (NewsAPI + RSS storage only)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Query

from src.api.rest.v1.schemas import NewsItemResponse, SearchNewsResponse
from src.core.config.settings import settings
from src.core.security import get_current_user
from src.infrastructure.data_collection import AlphaVantageNewsCollector, NewsAPIArticle, NewsAPICollector
from src.infrastructure.database.mongo_session import get_news_collection

router = APIRouter(prefix="/news", tags=["news"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=SearchNewsResponse)
async def list_news(
    query_text: str | None = Query(default=None, min_length=2),
    source: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> SearchNewsResponse:
    """List stored news articles (no event creation)."""
    collection = get_news_collection()
    if collection is None:
        fallback = _load_news_fallback()
        if not fallback:
            return SearchNewsResponse(items=[], page=page, page_size=page_size, total=0)
        items = _filter_items(fallback, query_text=query_text, source=source)
        total = len(items)
        paged = items[(page - 1) * page_size : (page - 1) * page_size + page_size]
        return SearchNewsResponse(items=paged, page=page, page_size=page_size, total=total)
    total_available = int(await collection.count_documents({}))
    if total_available == 0:
        fallback = _load_news_fallback()
        if not fallback:
            return SearchNewsResponse(items=[], page=page, page_size=page_size, total=0)
        items = _filter_items(fallback, query_text=query_text, source=source)
        total = len(items)
        paged = items[(page - 1) * page_size : (page - 1) * page_size + page_size]
        return SearchNewsResponse(items=paged, page=page, page_size=page_size, total=total)
    mongo_filter: dict[str, Any] = {}
    if source:
        mongo_filter["source"] = source
    if query_text:
        regex = {"$regex": query_text, "$options": "i"}
        mongo_filter["$or"] = [{"title": regex}, {"summary": regex}]
    total = int(await collection.count_documents(mongo_filter))
    cursor = (
        collection.find(mongo_filter)
        .sort("published_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    items = []
    async for doc in cursor:
        items.append(
            NewsItemResponse(
                article_id=str(doc.get("_id") or doc.get("article_id")),
                source=doc.get("source", "newsapi"),
                title=doc.get("title", ""),
                summary=doc.get("summary", ""),
                url=doc.get("url", ""),
                published_at=doc.get("published_at") or datetime.now(tz=UTC),
                author=doc.get("author"),
            )
        )
    return SearchNewsResponse(items=items, page=page, page_size=page_size, total=total)


@router.post("/refresh", response_model=SearchNewsResponse)
async def refresh_news(
    query_text: str | None = Query(default=None, min_length=2),
    sources: str | None = Query(default=None),
    mode: str = Query(default="top"),
    provider: str = Query(default="newsapi", pattern="^(newsapi|alphavantage|combined)$"),
) -> SearchNewsResponse:
    """Fetch latest news from configured providers and store it (no event creation)."""
    collectors: list[tuple[str, object]] = []
    if provider in {"newsapi", "combined"} and settings.newsapi_api_key:
        collectors.append(("newsapi", NewsAPICollector(api_key=settings.newsapi_api_key)))
    if provider in {"alphavantage", "combined"} and settings.alphavantage_api_key:
        collectors.append(("alphavantage", AlphaVantageNewsCollector(api_key=settings.alphavantage_api_key)))
    if not collectors:
        return SearchNewsResponse(items=[], page=1, page_size=0, total=0)

    collected: list[NewsAPIArticle] = []
    query = query_text or settings.newsapi_query
    source_filter = sources or settings.newsapi_sources or None
    for provider_name, collector in collectors:
        try:
            if provider_name == "newsapi":
                if mode == "everything":
                    from_date = (datetime.now(tz=UTC) - timedelta(days=2)).strftime("%Y-%m-%d")
                    articles = await collector.fetch_everything(
                        query=query,
                        sources=source_filter,
                        language=settings.newsapi_language,
                        page_size=settings.newsapi_page_size,
                        from_date=from_date,
                    )
                else:
                    articles = await collector.fetch_top_headlines(
                        query=query,
                        sources=source_filter,
                        language=settings.newsapi_language,
                        page_size=settings.newsapi_page_size,
                    )
            else:
                articles = await collector.fetch_news(query=query, limit=settings.alphavantage_page_size)
            collected.extend(articles)
        finally:
            try:
                await collector.close()  # type: ignore[func-returns-value]
            except Exception:
                pass
    collection = get_news_collection()
    if collection is None:
        return SearchNewsResponse(items=[], page=1, page_size=0, total=0)
    if collected:
        collected.sort(key=lambda item: item.published_at, reverse=True)
        for item in collected:
            doc = {
                "_id": item.article_id,
                "source": item.source,
                "title": item.title,
                "summary": item.summary,
                "url": item.url,
                "published_at": item.published_at,
                "author": item.author,
            }
            await collection.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
    return SearchNewsResponse(
        items=[
            NewsItemResponse(
                article_id=item.article_id,
                source=item.source,
                title=item.title,
                summary=item.summary,
                url=item.url,
                published_at=item.published_at,
                author=item.author,
            )
            for item in collected
        ],
        page=1,
        page_size=len(collected),
        total=len(collected),
    )


def _load_news_fallback() -> list[NewsItemResponse]:
    candidates = [Path(settings.data_dir) / "newsapi.json", Path(settings.data_dir) / "alphavantage.json"]
    items: list[NewsItemResponse] = []
    for data_path in candidates:
        if not data_path.exists():
            continue
        try:
            payload = data_path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            raw = json.loads(payload)
        except Exception:  # noqa: BLE001
            continue
        for entry in raw if isinstance(raw, list) else []:
            if not isinstance(entry, dict):
                continue
            published_raw = entry.get("published_at")
            published_at = datetime.now(tz=UTC)
            if isinstance(published_raw, str):
                try:
                    published_at = datetime.fromisoformat(published_raw)
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=UTC)
                except ValueError:
                    published_at = datetime.now(tz=UTC)
            items.append(
                NewsItemResponse(
                    article_id=str(entry.get("article_id", "")),
                    source=str(entry.get("source", "newsapi")),
                    title=str(entry.get("title", "")),
                    summary=str(entry.get("summary", "")),
                    url=str(entry.get("url", "")),
                    published_at=published_at,
                    author=entry.get("author"),
                )
            )
    items.sort(key=lambda item: item.published_at, reverse=True)
    return items


def _filter_items(
    items: list[NewsItemResponse],
    *,
    query_text: str | None,
    source: str | None,
) -> list[NewsItemResponse]:
    filtered = []
    for item in items:
        if source and item.source != source:
            continue
        if query_text:
            query = query_text.lower()
            if query not in item.title.lower() and query not in item.summary.lower():
                continue
        filtered.append(item)
    filtered.sort(key=lambda item: item.published_at, reverse=True)
    return filtered
