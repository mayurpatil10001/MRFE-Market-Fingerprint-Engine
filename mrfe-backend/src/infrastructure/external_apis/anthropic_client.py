"""Anthropic Claude API client wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from src.core.config.settings import settings
from src.core.logging import get_logger
from src.infrastructure.external_apis.llm_client import LLMClient, LLMResponse, LLMUsage

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _AnthropicContentBlock:
    """Anthropic message content block."""

    type: str
    text: str


class AnthropicClient(LLMClient):
    """Minimal async Anthropic client adhering to the shared LLM client contract."""

    provider = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self._client = httpx.AsyncClient(
            base_url=settings.anthropic_base_url.rstrip("/"),
            timeout=settings.anthropic_timeout_seconds,
            headers={
                "x-api-key": self.api_key or "",
                "anthropic-version": settings.anthropic_version,
                "content-type": "application/json",
            },
        )

    async def complete_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> LLMResponse | None:
        """Call Anthropic Messages API and normalize the response."""
        if not self.api_key:
            return None
        payload = self._build_payload(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)
        try:
            response = await self._client.post("/v1/messages", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("anthropic_request_failed", error=str(exc))
            return None
        data = response.json()
        usage = self._parse_usage(data.get("usage", {}))
        content = self._extract_text(data.get("content"))
        if content is None:
            return None
        return LLMResponse(
            provider=self.provider,
            model=payload["model"],
            content=content,
            raw=data,
            usage=usage,
        )

    def _build_payload(
        self,
        *,
        messages: list[dict[str, str]],
        model: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        system_parts = [msg["content"] for msg in messages if msg.get("role") == "system" and msg.get("content")]
        chat_messages = [
            {"role": "user" if msg.get("role") == "user" else "assistant", "content": msg.get("content", "")}
            for msg in messages
            if msg.get("role") != "system"
        ]
        payload: dict[str, Any] = {
            "model": model or settings.anthropic_model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max(1, max_tokens),
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        return payload

    @staticmethod
    def _extract_text(blocks: Any) -> str | None:
        if not isinstance(blocks, list):
            return None
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    return text
        return None

    @staticmethod
    def _parse_usage(raw: dict[str, Any]) -> LLMUsage:
        def to_int(value: Any) -> int | None:
            if isinstance(value, bool):
                return None
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            if isinstance(value, str):
                try:
                    return int(float(value))
                except ValueError:
                    return None
            return None

        return LLMUsage(
            prompt_tokens=to_int(raw.get("input_tokens")),
            completion_tokens=to_int(raw.get("output_tokens")),
            total_tokens=to_int(raw.get("input_tokens")) + to_int(raw.get("output_tokens"))
            if to_int(raw.get("input_tokens")) is not None and to_int(raw.get("output_tokens")) is not None
            else None,
            estimated_cost_usd=None,
        )

    async def close(self) -> None:
        """Close underlying HTTP resources."""
        await self._client.aclose()
