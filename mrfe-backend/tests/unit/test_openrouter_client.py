"""Unit tests for OpenRouter client retry and fallback behavior."""

from __future__ import annotations

import httpx
import pytest

from src.core.config.settings import settings
from src.infrastructure.external_apis.openrouter_client import OpenRouterClient


@pytest.mark.asyncio
async def test_openrouter_client_returns_none_without_api_key() -> None:
    """Client should no-op when API key is not configured."""
    original_key = settings.openrouter_api_key
    settings.openrouter_api_key = None
    client = OpenRouterClient(api_key=None)
    try:
        result = await client.complete_chat(messages=[{"role": "user", "content": "hello"}])
        assert result is None
    finally:
        await client.close()
        settings.openrouter_api_key = original_key


@pytest.mark.asyncio
async def test_openrouter_client_uses_fallback_model_on_primary_failure() -> None:
    """Fallback model should be used when primary model fails with retryable status."""
    original_primary = settings.openrouter_primary_model
    original_fallback = settings.openrouter_fallback_model
    original_retries = settings.openrouter_max_retries
    settings.openrouter_primary_model = "primary-model"
    settings.openrouter_fallback_model = "fallback-model"
    settings.openrouter_max_retries = 0

    call_models: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.read().decode("utf-8")
        if "primary-model" in payload:
            call_models.append("primary-model")
            return httpx.Response(status_code=503, json={"error": "upstream unavailable"})
        call_models.append("fallback-model")
        return httpx.Response(
            status_code=200,
            json={
                "choices": [{"message": {"content": "{\"summary\":\"ok\"}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )

    transport = httpx.MockTransport(handler)
    client = OpenRouterClient(api_key="test-key")
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=settings.openrouter_base_url.rstrip("/"),
        timeout=settings.openrouter_timeout_seconds,
        transport=transport,
        headers=client._headers(),
    )
    try:
        result = await client.complete_chat(messages=[{"role": "user", "content": "hello"}])
        assert result is not None
        assert result.model == "fallback-model"
        assert call_models == ["primary-model", "fallback-model"]
    finally:
        await client.close()
        settings.openrouter_primary_model = original_primary
        settings.openrouter_fallback_model = original_fallback
        settings.openrouter_max_retries = original_retries


@pytest.mark.asyncio
async def test_openrouter_client_blocks_when_cost_cap_exceeded() -> None:
    """Response should be dropped when per-request cost exceeds configured cap."""
    original_per_request_cap = settings.openrouter_max_cost_usd_per_request
    settings.openrouter_max_cost_usd_per_request = 0.001

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "choices": [{"message": {"content": "{\"summary\":\"ok\"}"}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200, "cost": 0.01},
            },
        )

    transport = httpx.MockTransport(handler)
    client = OpenRouterClient(api_key="test-key")
    await client._client.aclose()
    client._client = httpx.AsyncClient(
        base_url=settings.openrouter_base_url.rstrip("/"),
        timeout=settings.openrouter_timeout_seconds,
        transport=transport,
        headers=client._headers(),
    )
    try:
        result = await client.complete_chat(messages=[{"role": "user", "content": "hello"}])
        assert result is None
    finally:
        await client.close()
        settings.openrouter_max_cost_usd_per_request = original_per_request_cap
