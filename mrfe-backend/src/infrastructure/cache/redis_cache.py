"""Redis cache service with cache-aside pattern."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

from redis.asyncio import Redis

from src.core.config.settings import settings


class RedisCacheService:
    """Enterprise cache helper with invalidation/pub-sub support."""

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    @classmethod
    def from_url(cls, url: str | None = None) -> "RedisCacheService":
        """Build cache service from Redis URL."""
        client = Redis.from_url(url or settings.redis_url, decode_responses=True)
        return cls(redis_client=client)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        """Return decoded JSON payload by key."""
        raw = await self._redis.get(key)
        if raw is None:
            return None
        return cast(dict[str, Any], json.loads(raw))

    async def set_json(self, key: str, payload: dict[str, Any], ttl_seconds: int | None = None) -> None:
        """Set JSON payload with optional TTL."""
        await self._redis.set(
            key,
            json.dumps(payload, separators=(",", ":")),
            ex=ttl_seconds or settings.redis_ttl,
        )

    async def delete(self, key: str) -> None:
        """Delete key."""
        await self._redis.delete(key)

    async def publish_invalidation(self, cache_key: str) -> None:
        """Publish cache invalidation event."""
        await self._redis.publish("mrfe:cache:invalidate", cache_key)

    async def warm(self, pairs: dict[str, dict[str, Any]], ttl_seconds: int | None = None) -> None:
        """Warm cache with key-value payload pairs."""
        pipe = self._redis.pipeline(transaction=False)
        for key, payload in pairs.items():
            pipe.set(key, json.dumps(payload, separators=(",", ":")), ex=ttl_seconds or settings.redis_ttl)
        await pipe.execute()

    @asynccontextmanager
    async def distributed_lock(self, key: str, timeout_seconds: int = 10) -> AsyncIterator[bool]:
        """Acquire/release distributed lock."""
        lock = self._redis.lock(name=f"lock:{key}", timeout=timeout_seconds)
        acquired = await lock.acquire(blocking=False)
        try:
            yield acquired
        finally:
            if acquired:
                await lock.release()
