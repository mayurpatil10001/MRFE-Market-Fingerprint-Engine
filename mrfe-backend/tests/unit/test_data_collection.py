"""Unit tests for data collection pipeline utilities."""

from __future__ import annotations

import httpx
import pytest

from src.infrastructure.data_collection.macro_collector import FREDMacroCollector
from src.infrastructure.data_collection.market_collector import MarketDataCollector
from src.infrastructure.data_collection.news_collector import NewsCollector


@pytest.mark.asyncio
async def test_market_collector_parses_csv() -> None:
    csv_payload = "Date,Open,High,Low,Close,Volume\n2026-02-01,100,101,99,100.5,12345\n"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, text=csv_payload)

    collector = MarketDataCollector()
    await collector._client.aclose()
    collector._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        candles = await collector.fetch_daily_history("SPY")
    finally:
        await collector.close()
    assert len(candles) == 1
    assert candles[0].symbol == "SPY"
    assert candles[0].close == 100.5


@pytest.mark.asyncio
async def test_news_collector_parses_and_deduplicates() -> None:
    rss_payload = """
    <rss><channel>
      <item><title>Headline A</title><description>Summary A</description><link>https://a</link></item>
      <item><title>Headline A</title><description>Summary A</description><link>https://a</link></item>
    </channel></rss>
    """

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, text=rss_payload)

    collector = NewsCollector()
    await collector._client.aclose()
    collector._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        articles = await collector.fetch_rss(source_name="test", feed_url="https://example.test/rss")
    finally:
        await collector.close()
    deduped = collector.deduplicate(articles)
    assert len(articles) == 2
    assert len(deduped) == 1


@pytest.mark.asyncio
async def test_macro_collector_parses_observations() -> None:
    payload = {
        "observations": [
            {"date": "2026-01-01", "value": "2.1"},
            {"date": "2026-01-02", "value": "."},
        ]
    }

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, json=payload)

    collector = FREDMacroCollector(api_key="x")
    await collector._client.aclose()
    collector._client = httpx.AsyncClient(
        base_url="https://api.stlouisfed.org/fred",
        transport=httpx.MockTransport(handler),
    )
    try:
        rows = await collector.fetch_series("CPIAUCSL")
    finally:
        await collector.close()
    assert len(rows) == 1
    assert rows[0].series_id == "CPIAUCSL"
