"""Daily collection entrypoint for market/news/macro datasets."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from src.infrastructure.data_collection import (
    FREDMacroCollector,
    MarketDataCollector,
    NewsCollector,
    NewsAPICollector,
)
from src.core.config.settings import settings


async def main() -> None:
    output_dir = Path(os.getenv("MRFE_DATA_DIR", settings.data_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    market = MarketDataCollector()
    news = NewsCollector()
    newsapi = NewsAPICollector(api_key=settings.newsapi_api_key)
    fred_key = os.getenv("FRED_API_KEY", settings.fred_api_key or "")
    macro = FREDMacroCollector(api_key=fred_key) if fred_key else None

    try:
        symbols = ["SPY", "QQQ", "GLD", "TLT"]
        for symbol in symbols:
            candles = await market.fetch_daily_history(symbol=symbol)
            await market.save_as_parquet_or_jsonl(
                candles=candles,
                output_path=str(output_dir / f"market_{symbol.lower()}.parquet"),
            )

        feeds = {
            "reuters": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
            "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        }
        all_articles = []
        for source, url in feeds.items():
            all_articles.extend(await news.fetch_rss(source_name=source, feed_url=url))
        unique_articles = news.deduplicate(all_articles)
        (output_dir / "news_count.txt").write_text(str(len(unique_articles)), encoding="utf-8")
        if settings.newsapi_api_key:
            newsapi_articles = await newsapi.fetch_top_headlines(
                query=settings.newsapi_query,
                sources=settings.newsapi_sources or None,
                language=settings.newsapi_language,
                page_size=settings.newsapi_page_size,
            )
            (output_dir / "newsapi_count.txt").write_text(str(len(newsapi_articles)), encoding="utf-8")
            payload = [
                {
                    **article.__dict__,
                    "published_at": article.published_at.isoformat(),
                }
                for article in newsapi_articles
            ]
            (output_dir / "newsapi.json").write_text(json.dumps(payload), encoding="utf-8")

        if macro is not None:
            for series in ("CPIAUCSL", "UNRATE", "FEDFUNDS"):
                observations = await macro.fetch_series(series_id=series)
                rows = macro.to_postgres_rows(observations)
                (output_dir / f"macro_{series.lower()}.json").write_text(str(rows), encoding="utf-8")
    finally:
        await market.close()
        await news.close()
        await newsapi.close()
        if macro is not None:
            await macro.close()


if __name__ == "__main__":
    asyncio.run(main())
