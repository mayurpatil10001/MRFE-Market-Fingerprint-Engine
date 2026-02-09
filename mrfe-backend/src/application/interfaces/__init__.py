
"""Application layer interfaces."""

from __future__ import annotations

from typing import Protocol, TypeVar

TCommand = TypeVar("TCommand", contravariant=True)
TQuery = TypeVar("TQuery", contravariant=True)
TResult = TypeVar("TResult", covariant=True)


class CommandHandler(Protocol[TCommand, TResult]):
    """Generic command handler contract."""

    async def execute(self, command: TCommand) -> TResult:
        """Execute command."""


class QueryHandler(Protocol[TQuery, TResult]):
    """Generic query handler contract."""

    async def execute(self, query: TQuery) -> TResult:
        """Execute query."""
