"""OpenRouter API client wrapper."""

from __future__ import annotations

import asyncio
import time
from typing import Any, cast

import httpx

from src.core.config.settings import settings
from src.core.logging import get_logger
from src.core.monitoring.metrics import (
    llm_cost_usd_total,
    llm_request_duration_seconds,
    llm_requests_total,
    llm_tokens_total,
)
from src.infrastructure.external_apis.llm_client import LLMClient, LLMResponse, LLMUsage

logger = get_logger(__name__)


class OpenRouterClient(LLMClient):
    """Minimal async OpenRouter client with retry-safe call surface."""

    provider = "openrouter"
    _budget_lock = asyncio.Lock()
    _spent_usd = 0.0

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=settings.openrouter_timeout_seconds,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        """Build default request headers for OpenRouter."""
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_http_referer,
            "X-Title": settings.openrouter_x_title,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def complete_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> LLMResponse | None:
        """Call OpenRouter with model fallback and retries."""
        if not self.api_key:
            return None
        if not await self._budget_available():
            llm_requests_total.labels(
                provider=self.provider,
                model=(model or settings.openrouter_primary_model),
                status="budget_blocked",
            ).inc()
            return None
        primary = model or settings.openrouter_primary_model
        fallback = settings.openrouter_fallback_model
        models = [primary]
        if fallback and fallback != primary:
            models.append(fallback)
        for candidate_model in models:
            result = await self._request_with_retries(
                messages=messages,
                model=candidate_model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if result is not None:
                return result
        return None

    async def _request_with_retries(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse | None:
        """Request one model with bounded exponential backoff."""
        max_retries = max(0, settings.openrouter_max_retries)
        for attempt in range(max_retries + 1):
            started = time.perf_counter()
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                latency = time.perf_counter() - started
                llm_request_duration_seconds.labels(provider=self.provider, model=model).observe(latency)
                if response.status_code in {429, 500, 502, 503, 504}:
                    llm_requests_total.labels(
                        provider=self.provider,
                        model=model,
                        status=f"http_{response.status_code}",
                    ).inc()
                    if attempt < max_retries:
                        await asyncio.sleep(min(2.0, 0.25 * (2**attempt)))
                        continue
                    logger.warning(
                        "openrouter_retryable_status_exhausted",
                        model=model,
                        status_code=response.status_code,
                    )
                    return None
                response.raise_for_status()
                payload = cast(dict[str, Any], response.json())
                result = self._to_response(model=model, payload=payload)
                if not await self._allow_response_under_cost_caps(model=model, usage=result.usage):
                    llm_requests_total.labels(provider=self.provider, model=model, status="cost_blocked").inc()
                    return None
                llm_requests_total.labels(provider=self.provider, model=model, status="success").inc()
                self._record_usage(model=model, usage=result.usage)
                return result
            except httpx.TimeoutException as exc:
                llm_requests_total.labels(provider=self.provider, model=model, status="timeout").inc()
                if attempt < max_retries:
                    await asyncio.sleep(min(2.0, 0.25 * (2**attempt)))
                    continue
                logger.warning("openrouter_timeout_exhausted", model=model, error=str(exc))
                return None
            except httpx.HTTPError as exc:
                llm_requests_total.labels(provider=self.provider, model=model, status="http_error").inc()
                logger.warning("openrouter_request_failed", model=model, error=str(exc))
                return None
        return None

    @staticmethod
    def _extract_content(payload: dict[str, Any]) -> str:
        """Extract first choice message content from payload."""
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message")
        if not isinstance(message, dict):
            return ""
        content = message.get("content")
        return content if isinstance(content, str) else ""

    def _to_response(self, model: str, payload: dict[str, Any]) -> LLMResponse:
        """Normalize OpenRouter payload to provider-agnostic response."""
        usage_raw = payload.get("usage")
        usage = self._to_usage(usage_raw if isinstance(usage_raw, dict) else {})
        return LLMResponse(
            provider=self.provider,
            model=model,
            content=self._extract_content(payload),
            raw=payload,
            usage=usage,
        )

    @staticmethod
    def _to_usage(raw_usage: dict[str, Any]) -> LLMUsage:
        """Parse OpenRouter usage payload into typed metadata."""

        def to_int(name: str) -> int | None:
            value = raw_usage.get(name)
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

        def to_float(name: str) -> float | None:
            value = raw_usage.get(name)
            if isinstance(value, bool):
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return None
            return None

        cost = (
            to_float("cost")
            or to_float("total_cost")
            or to_float("estimated_cost")
            or to_float("total_cost_usd")
        )
        return LLMUsage(
            prompt_tokens=to_int("prompt_tokens"),
            completion_tokens=to_int("completion_tokens"),
            total_tokens=to_int("total_tokens"),
            estimated_cost_usd=cost,
        )

    def _record_usage(self, model: str, usage: LLMUsage) -> None:
        """Publish usage metrics for observability and budget controls."""
        if usage.prompt_tokens is not None:
            llm_tokens_total.labels(
                provider=self.provider,
                model=model,
                token_type="prompt",
            ).inc(usage.prompt_tokens)
        if usage.completion_tokens is not None:
            llm_tokens_total.labels(
                provider=self.provider,
                model=model,
                token_type="completion",
            ).inc(usage.completion_tokens)
        if usage.total_tokens is not None:
            llm_tokens_total.labels(
                provider=self.provider,
                model=model,
                token_type="total",
            ).inc(usage.total_tokens)
        if usage.estimated_cost_usd is not None and usage.estimated_cost_usd > 0:
            llm_cost_usd_total.labels(provider=self.provider, model=model).inc(usage.estimated_cost_usd)

    async def _budget_available(self) -> bool:
        """Check if the configured monthly budget is exhausted."""
        budget = settings.openrouter_monthly_budget_usd
        if budget <= 0:
            return True
        async with self._budget_lock:
            if self._spent_usd >= budget:
                logger.warning(
                    "openrouter_budget_exhausted",
                    spent_usd=round(self._spent_usd, 6),
                    budget_usd=round(budget, 6),
                )
                return False
        return True

    async def _allow_response_under_cost_caps(self, model: str, usage: LLMUsage) -> bool:
        """Validate per-request and rolling budget caps."""
        cost = usage.estimated_cost_usd
        if cost is None or cost <= 0:
            return True
        max_per_request = settings.openrouter_max_cost_usd_per_request
        if max_per_request > 0 and cost > max_per_request:
            logger.warning(
                "openrouter_cost_per_request_exceeded",
                model=model,
                cost_usd=round(cost, 6),
                max_cost_usd=round(max_per_request, 6),
            )
            return False
        budget = settings.openrouter_monthly_budget_usd
        async with self._budget_lock:
            projected = self._spent_usd + cost
            if budget > 0 and projected > budget:
                logger.warning(
                    "openrouter_monthly_budget_projection_exceeded",
                    model=model,
                    spent_usd=round(self._spent_usd, 6),
                    request_cost_usd=round(cost, 6),
                    budget_usd=round(budget, 6),
                )
                return False
            self._spent_usd = projected
        return True

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str = "openai/gpt-4o-mini",
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> dict[str, Any] | None:
        """Backward-compatible API returning the raw provider payload."""
        result = await self.complete_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result.raw if result is not None else None

    async def close(self) -> None:
        """Close underlying HTTP client."""
        await self._client.aclose()
