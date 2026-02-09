"""Request metrics middleware."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.core.monitoring.metrics import (
    active_requests,
    http_request_duration_seconds,
    http_requests_total,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect Prometheus metrics for HTTP traffic."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        method = request.method
        path = request.url.path
        status_code = "500"
        active_requests.inc()
        started = time.perf_counter()
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        finally:
            elapsed = time.perf_counter() - started
            active_requests.dec()
            http_request_duration_seconds.labels(method=method, path=path).observe(elapsed)
            http_requests_total.labels(method=method, path=path, status_code=status_code).inc()
