"""In-memory rate limiting middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.core.config.settings import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter by user or IP."""

    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._window_seconds = 60
        self._limit = settings.rate_limit_per_minute
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        identity = self._identity(request)
        now = time.time()
        bucket = self._buckets[identity]
        while bucket and now - bucket[0] > self._window_seconds:
            bucket.popleft()
        if len(bucket) >= self._limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "rate limit exceeded"},
            )
        bucket.append(now)
        return await call_next(request)

    @staticmethod
    def _identity(request: Request) -> str:
        """Choose user identity if authenticated else fallback to IP."""
        auth = request.headers.get("authorization", "")
        if auth:
            return f"auth:{auth[-20:]}"
        client = request.client.host if request.client else "unknown"
        return f"ip:{client}"
