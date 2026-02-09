"""MongoDB client lifecycle and helpers."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

from src.core.config.settings import settings

_client: AsyncIOMotorClient | None = None


def init() -> None:
    """Initialize the Mongo client."""
    global _client
    if settings.mongo_url and _client is None:
        _client = AsyncIOMotorClient(settings.mongo_url)


def get_client() -> AsyncIOMotorClient | None:
    """Return Mongo client if initialized."""
    return _client


def get_database() -> Any | None:
    """Return configured Mongo database."""
    client = get_client()
    if client is None:
        return None
    return client[settings.mongo_database]


def get_news_collection() -> Any | None:
    """Return Mongo collection for news ingestion."""
    db = get_database()
    if db is None:
        return None
    return db[settings.mongo_news_collection]


async def close() -> None:
    """Close Mongo client."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
