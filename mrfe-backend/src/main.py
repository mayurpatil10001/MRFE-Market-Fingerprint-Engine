"""MRFE FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from src.api.rest import api_v1_router
from src.api.rest.middleware import (
    MetricsMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from src.api.websocket import websocket_router
from src.core.config.settings import settings
from src.core.logging import configure_logging, get_logger
from src.core.monitoring import configure_tracing
from src.core.utils.exception_handler import register_exception_handlers
from src.infrastructure.database.models import Base
from src.infrastructure.database.mongo_session import close as close_mongo, init as init_mongo
from src.infrastructure.database.session import session_manager
from src.infrastructure.demo_seed import seed_demo_data


def _configure_sentry() -> None:
    """Initialize Sentry only when configured and available."""
    if not settings.sentry_dsn:
        return
    try:
        import sentry_sdk
    except ImportError:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.2,
        environment=settings.environment.value,
        release=settings.app_version,
    )


configure_logging()
_configure_sentry()
logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INDEX_FILE = PROJECT_ROOT / "index.html"
PUBLIC_DIR = PROJECT_ROOT / "public"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown lifecycle."""
    session_manager.init()
    init_mongo()
    async with session_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        async with session_manager.session() as session:
            await seed_demo_data(session)
    except Exception as exc:  # noqa: BLE001
        logger.warning("demo_seed_failed", error=str(exc))
    logger.info("app_started", version=settings.app_version, environment=settings.environment.value)
    yield
    await session_manager.dispose()
    await close_mongo()
    logger.info("app_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

configure_tracing(app)
register_exception_handlers(app)
app.include_router(api_v1_router)
app.include_router(websocket_router)
if PUBLIC_DIR.exists():
    app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/", include_in_schema=False, response_model=None)
async def root() -> Response:
    """Serve dashboard frontend from project root."""
    frontend_index = FRONTEND_DIST / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse({"service": settings.app_name, "version": settings.app_version})


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str) -> Response:
    """Serve SPA routes without intercepting API/static/system paths."""
    blocked_prefixes = ("api/", "docs", "openapi.json", "metrics", "health", "ws/", "public/", "assets/")
    if full_path == "" or any(full_path.startswith(prefix) for prefix in blocked_prefixes):
        return JSONResponse({"detail": "not found"}, status_code=404)
    frontend_index = FRONTEND_DIST / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return JSONResponse({"detail": "not found"}, status_code=404)
