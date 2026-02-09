"""Async database engine/session management."""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config.settings import settings
from src.core.logging import get_logger
from src.core.monitoring.metrics import slow_query_total

logger = get_logger(__name__)


class SessionManager:
    """Centralized SQLAlchemy async session manager with pooling."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_maker: async_sessionmaker[AsyncSession] | None = None

    def init(self, database_url: str | None = None) -> None:
        """Initialize engine and session maker."""
        url = database_url or settings.database_url
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {
            "echo": settings.database_echo,
            "pool_pre_ping": True,
            "connect_args": connect_args,
        }
        if url.startswith("sqlite+aiosqlite"):
            connect_args["check_same_thread"] = False
        else:
            engine_kwargs["pool_size"] = settings.database_pool_size
            engine_kwargs["max_overflow"] = settings.database_max_overflow
        self._engine = create_async_engine(url, **engine_kwargs)
        self._register_slow_query_logging(self._engine)
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            class_=AsyncSession,
            autoflush=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Return initialized engine."""
        if self._engine is None:
            raise RuntimeError("session manager is not initialized")
        return self._engine

    def session(self) -> AsyncSession:
        """Create async session."""
        if self._session_maker is None:
            raise RuntimeError("session manager is not initialized")
        return self._session_maker()

    async def dispose(self) -> None:
        """Dispose engine resources."""
        if self._engine is not None:
            await self._engine.dispose()

    @staticmethod
    def _register_slow_query_logging(engine: AsyncEngine) -> None:
        """Register SQL timing hooks for slow query monitoring."""

        @event.listens_for(engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
            conn.info.setdefault("query_start_time", []).append(time.perf_counter())

        @event.listens_for(engine.sync_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):  # type: ignore[no-untyped-def]
            start = conn.info["query_start_time"].pop(-1)
            elapsed = time.perf_counter() - start
            if elapsed > 0.2:
                slow_query_total.labels(query_name="sqlalchemy").inc()
                logger.warning("slow_query", elapsed_ms=round(elapsed * 1000, 2), statement=statement[:120])


session_manager = SessionManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for DB session."""
    async with session_manager.session() as session:
        yield session
