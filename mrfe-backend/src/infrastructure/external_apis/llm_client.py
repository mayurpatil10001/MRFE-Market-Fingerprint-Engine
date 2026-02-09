"""Provider-agnostic LLM client contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class LLMUsage:
    """Usage and billing metadata for one LLM call."""

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost_usd: float | None = None


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """Normalized response payload for chat-completion style calls."""

    provider: str
    model: str
    content: str
    raw: dict[str, Any]
    usage: LLMUsage


class LLMClient(Protocol):
    """Provider-agnostic async chat completion interface."""

    async def complete_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> LLMResponse | None:
        """Complete a chat request."""

    async def close(self) -> None:
        """Close any underlying network resources."""
