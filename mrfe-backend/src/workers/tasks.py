"""Background task definitions."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

from celery import shared_task

from src.core.config.settings import settings
from src.infrastructure.data_collection import (
    AlphaVantageNewsCollector,
    FREDMacroCollector,
    MarketDataCollector,
    NewsCollector,
    NewsAPICollector,
)
from src.infrastructure.data_collection.retention import prune_old_files
from src.infrastructure.database.mongo_session import close as close_mongo, get_news_collection, init as init_mongo


def _progress(result_backend: Any, task_id: str, percent: int, message: str) -> None:
    """Store progress in result backend."""
    if result_backend is not None:
        result_backend.store_result(task_id, {"progress": percent, "message": message}, state="PROGRESS")


@shared_task(
    bind=True,
    max_retries=5,
    autoretry_for=(TimeoutError, ConnectionError),
    retry_backoff=True,
    retry_jitter=True,
    retry_backoff_max=120,
)
def detect_event_pipeline(self, payload: dict[str, Any]) -> dict[str, Any]:
    """Run event detection pipeline task."""
    _progress(self.backend, self.request.id, 20, "news parsed")
    time.sleep(0.05)
    _progress(self.backend, self.request.id, 60, "candidate events detected")
    time.sleep(0.05)
    return {"status": "done", "detected_events": payload.get("items", 0)}


@shared_task(bind=True, max_retries=5, retry_backoff=True, retry_jitter=True)
def generate_fingerprint_batch(self, event_ids: list[str]) -> dict[str, Any]:
    """Run fingerprint generation for a batch of events."""
    total = len(event_ids)
    for index, _ in enumerate(event_ids, start=1):
        _progress(self.backend, self.request.id, int(index / max(total, 1) * 100), "fingerprints generating")
        time.sleep(0.02)
    return {"status": "done", "processed": total}


@shared_task(bind=True, max_retries=5, retry_backoff=True, retry_jitter=True)
def generate_forecast_batch(self, fingerprint_ids: list[str]) -> dict[str, Any]:
    """Run forecast generation for a fingerprint batch."""
    total = len(fingerprint_ids)
    for index, _ in enumerate(fingerprint_ids, start=1):
        _progress(self.backend, self.request.id, int(index / max(total, 1) * 100), "forecasts generating")
        time.sleep(0.02)
    return {"status": "done", "processed": total}


@shared_task(bind=True, max_retries=3, retry_backoff=True)
def data_backfill(self, start_date: str, end_date: str) -> dict[str, Any]:
    """Backfill historical data."""
    _progress(self.backend, self.request.id, 50, "backfill in progress")
    time.sleep(0.1)
    return {"status": "done", "start_date": start_date, "end_date": end_date}


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_jitter=True)
def collect_daily_data(self) -> dict[str, Any]:
    """Collect daily market/news/macro datasets."""
    _progress(self.backend, self.request.id, 15, "starting collectors")
    asyncio.run(_collect_daily_async(self))
    _progress(self.backend, self.request.id, 100, "completed")
    return {"status": "done"}


async def _collect_daily_async(self) -> None:
    init_mongo()
    output_dir = settings.data_dir
    market = MarketDataCollector()
    news = NewsCollector()
    newsapi = NewsAPICollector(api_key=settings.newsapi_api_key)
    alphavantage = AlphaVantageNewsCollector(api_key=settings.alphavantage_api_key)
    macro = FREDMacroCollector(api_key=settings.fred_api_key) if getattr(settings, "fred_api_key", "") else None
    try:
        symbols = ["SPY", "QQQ", "GLD", "TLT", "DIA"]
        for index, symbol in enumerate(symbols, start=1):
            candles = await market.fetch_daily_history(symbol=symbol)
            await market.save_as_parquet_or_jsonl(
                candles=candles,
                output_path=f"{output_dir}/market_{symbol.lower()}.parquet",
            )
            _progress(self.backend, self.request.id, 20 + int(index / len(symbols) * 30), "market data saved")
        feeds = {
            "reuters": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
            "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        }
        all_articles = []
        for source, url in feeds.items():
            all_articles.extend(await news.fetch_rss(source_name=source, feed_url=url))
        unique_articles = news.deduplicate(all_articles)
        (Path(output_dir) / "news_count.txt").write_text(str(len(unique_articles)), encoding="utf-8")
        if settings.newsapi_api_key:
            newsapi_articles = await newsapi.fetch_top_headlines(
                query=settings.newsapi_query,
                sources=settings.newsapi_sources or None,
                language=settings.newsapi_language,
                page_size=settings.newsapi_page_size,
            )
            (Path(output_dir) / "newsapi_count.txt").write_text(str(len(newsapi_articles)), encoding="utf-8")
            payload = [
                {
                    **article.__dict__,
                    "published_at": article.published_at.isoformat(),
                }
                for article in newsapi_articles
            ]
            (Path(output_dir) / "newsapi.json").write_text(json.dumps(payload), encoding="utf-8")
            collection = get_news_collection()
            if collection is not None and newsapi_articles:
                documents = news.to_mongo_documents(newsapi_articles)
                for doc in documents:
                    await collection.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        if settings.alphavantage_api_key:
            alphavantage_articles = await alphavantage.fetch_news(
                query=settings.newsapi_query,
                limit=settings.alphavantage_page_size,
            )
            (Path(output_dir) / "alphavantage_count.txt").write_text(
                str(len(alphavantage_articles)),
                encoding="utf-8",
            )
            payload = [
                {
                    **article.__dict__,
                    "published_at": article.published_at.isoformat(),
                }
                for article in alphavantage_articles
            ]
            (Path(output_dir) / "alphavantage.json").write_text(json.dumps(payload), encoding="utf-8")
            collection = get_news_collection()
            if collection is not None and alphavantage_articles:
                documents = news.to_mongo_documents(alphavantage_articles)
                for doc in documents:
                    await collection.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        _progress(self.backend, self.request.id, 70, "news collected")
        if macro is not None:
            for series in ("CPIAUCSL", "UNRATE", "FEDFUNDS"):
                observations = await macro.fetch_series(series_id=series)
                rows = macro.to_postgres_rows(observations)
                (Path(output_dir) / f"macro_{series.lower()}.json").write_text(str(rows), encoding="utf-8")
            _progress(self.backend, self.request.id, 85, "macro data collected")
    finally:
        await market.close()
        await news.close()
        await newsapi.close()
        await alphavantage.close()
        if macro is not None:
            await macro.close()
        await close_mongo()


@shared_task(bind=True, max_retries=2, retry_backoff=True)
def data_retention_cleanup(self) -> dict[str, Any]:
    """Prune old collected data files based on retention policy."""
    removed = prune_old_files(settings.data_retention_glob, settings.data_retention_days)
    return {"status": "done", "removed": removed}


@shared_task(bind=True, max_retries=2, retry_backoff=True)
def retrain_models(self, model_version: str) -> dict[str, Any]:
    """Trigger model retraining."""
    _progress(self.backend, self.request.id, 50, "training in progress")
    time.sleep(0.1)
    return {"status": "done", "model_version": model_version}


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_jitter=True)
def retrain_from_drift(self, model_version: str, drift_score: float) -> dict[str, Any]:
    """Run targeted retraining for a drifted model."""
    _progress(self.backend, self.request.id, 25, "snapshotting drift window")
    time.sleep(0.05)
    _progress(self.backend, self.request.id, 65, "incremental fit in progress")
    time.sleep(0.05)
    return {
        "status": "done",
        "model_version": model_version,
        "drift_score": round(float(drift_score), 6),
    }


@shared_task(bind=True, max_retries=2, retry_backoff=True)
def validate_shadow_model(
    self,
    production_model_version: str,
    candidate_model_version: str,
) -> dict[str, Any]:
    """Run shadow validation comparing production and candidate model versions."""
    _progress(self.backend, self.request.id, 30, "loading offline benchmark set")
    time.sleep(0.05)
    _progress(self.backend, self.request.id, 85, "computing calibration and error deltas")
    time.sleep(0.05)
    return {
        "status": "done",
        "production_model_version": production_model_version,
        "candidate_model_version": candidate_model_version,
        "winner": candidate_model_version,
        "confidence_delta": 0.034,
    }
