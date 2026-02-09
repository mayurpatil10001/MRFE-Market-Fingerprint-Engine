"""System endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response
from sqlalchemy import text

from src.core.monitoring.metrics import export_metrics
from src.infrastructure.database.session import session_manager

router = APIRouter(tags=["system"])


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness() -> dict[str, str]:
    """Readiness check endpoint with DB ping."""
    async with session_manager.session() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    payload, content_type = export_metrics()
    return Response(content=payload, media_type=content_type)
