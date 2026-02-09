"""Generic SQLAlchemy repository helpers."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

TModel = TypeVar("TModel")


class SQLAlchemyRepository(Generic[TModel]):
    """Base repository helper class."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
