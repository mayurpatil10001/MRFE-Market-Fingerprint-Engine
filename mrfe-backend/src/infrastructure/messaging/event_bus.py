"""In-process observer/event bus."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable

from src.domain.events import DomainEvent

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """Simple async observer bus."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register handler for event name."""
        self._handlers[event_name].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        """Publish event to all handlers."""
        for handler in self._handlers.get(event.name, []):
            await handler(event)
