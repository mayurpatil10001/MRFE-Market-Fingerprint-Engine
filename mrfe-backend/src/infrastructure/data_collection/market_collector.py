"""Market data collection utilities."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MarketCandle:
    """Normalized OHLCV candle."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketDataCollector:
    """Collect historical market candles from providers with local persistence helpers."""

    _stooq_url = "https://stooq.com/q/d/l/"

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self._client = httpx.AsyncClient(timeout=timeout_seconds)

    async def fetch_daily_history(self, symbol: str, interval: str = "d") -> list[MarketCandle]:
        """Fetch daily candles using a public CSV provider with resilient parsing."""
        normalized = symbol.upper().replace("^", "")
        params = {"s": f"{normalized}.us", "i": interval}
        response = await self._client.get(self._stooq_url, params=params)
        response.raise_for_status()
        rows = list(csv.DictReader(response.text.splitlines()))
        candles: list[MarketCandle] = []
        for row in rows:
            parsed = self._parse_row(symbol=normalized, row=row)
            if parsed is not None:
                candles.append(parsed)
        return candles

    @staticmethod
    def _parse_row(symbol: str, row: dict[str, str]) -> MarketCandle | None:
        """Parse one CSV row into a candle object."""
        try:
            timestamp = datetime.fromisoformat(row["Date"]).replace(tzinfo=UTC)
            return MarketCandle(
                symbol=symbol,
                timestamp=timestamp,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row.get("Volume", "0") or 0.0),
            )
        except (KeyError, ValueError):
            return None

    async def save_as_parquet_or_jsonl(self, candles: list[MarketCandle], output_path: str) -> Path:
        """Persist candles to parquet when available, otherwise JSON lines fallback."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        records = [asdict(item) for item in candles]
        try:
            import pandas as pd  # type: ignore[import-untyped]
        except ImportError:
            jsonl_path = path.with_suffix(".jsonl")
            lines = [self._to_json_line(record) for record in records]
            jsonl_path.write_text("".join(lines), encoding="utf-8")
            return jsonl_path
        dataframe = pd.DataFrame(records)
        dataframe.to_parquet(path, index=False)
        return path

    @staticmethod
    def _to_json_line(record: dict[str, Any]) -> str:
        timestamp = record["timestamp"]
        if isinstance(timestamp, datetime):
            record = dict(record)
            record["timestamp"] = timestamp.isoformat()
        import json

        return json.dumps(record, separators=(",", ":")) + "\n"

    async def close(self) -> None:
        """Close underlying HTTP resources."""
        await self._client.aclose()
