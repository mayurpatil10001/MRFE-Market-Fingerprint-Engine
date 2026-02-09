"""AI intelligence endpoints with pluggable LLM providers and resilient fallback."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Literal, cast

from fastapi import APIRouter, Depends

from src.api.rest.v1.schemas import GenerateIntelRequest, IntelResponse, IntelScenario
from src.core.config.settings import settings
from src.core.logging import get_logger
from src.core.security import get_current_user
from src.core.utils.common import sanitize_text
from src.infrastructure.external_apis import AnthropicClient, LLMClient, OpenRouterClient

logger = get_logger(__name__)

router = APIRouter(prefix="/intel", tags=["intel"], dependencies=[Depends(get_current_user)])


@router.get("/capabilities")
async def get_intel_capabilities() -> dict[str, object]:
    """Report AI intelligence capabilities for the active deployment."""
    return {
        "active_provider": settings.llm_provider,
        "providers": {
            "openrouter": {
                "available": bool(settings.openrouter_api_key),
                "primary_model": settings.openrouter_primary_model,
                "fallback_model": settings.openrouter_fallback_model,
            },
            "anthropic": {
                "available": bool(settings.anthropic_api_key),
                "primary_model": settings.anthropic_model,
            },
            "heuristic": {"available": True},
        },
        "fallback_mode": "deterministic_heuristics",
    }


@router.post("/brief", response_model=IntelResponse)
async def generate_intel_brief(payload: GenerateIntelRequest) -> IntelResponse:
    """Generate probabilistic market intelligence."""
    normalized_symbol = sanitize_text(payload.symbol).upper()
    normalized_context = sanitize_text(payload.market_context)
    fallback_response = _heuristic_intel(
        symbol=normalized_symbol,
        market_context=normalized_context,
        horizon_hours=payload.horizon_hours,
        risk_profile=payload.risk_profile,
        warnings=["LLM unavailable: using deterministic fallback mode."],
    )
    provider_choice, client = _select_llm_client(payload.provider)
    if client is None:
        return fallback_response

    model = payload.model or (
        settings.anthropic_model if provider_choice == "anthropic" else settings.openrouter_primary_model
    )
    try:
        llm_response = await client.complete_chat(
            model=model,
            temperature=0.15,
            max_tokens=700,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MRFE institutional market strategist. "
                        "Respond with valid JSON only, no markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Symbol: {normalized_symbol}\n"
                        f"HorizonHours: {payload.horizon_hours}\n"
                        f"RiskProfile: {payload.risk_profile}\n"
                        f"Context: {normalized_context}\n\n"
                        "Return JSON with keys: "
                        "summary (string), "
                        "key_drivers (array of 3-6 strings), "
                        "action_bias (bullish|bearish|neutral), "
                        "scenarios (array of exactly 3 objects with "
                        "name, probability, expected_move_percent, confidence, rationale)."
                    ),
                },
            ],
        )
    finally:
        await client.close()

    if llm_response is None:
        return fallback_response

    response = _parse_llm_response(
        completion=llm_response.raw,
        symbol=normalized_symbol,
    )
    if response is None:
        fallback_response.warnings = [
            "LLM response parsing failed: using deterministic fallback mode."
        ]
        return fallback_response
    response.provider = provider_choice
    response.model = model
    return response


def _select_llm_client(
    provider: str | None,
) -> tuple[str, LLMClient | None]:
    """Choose the best-available LLM provider based on request and configuration."""
    requested = (provider or settings.llm_provider).lower()
    if requested == "anthropic":
        if settings.anthropic_api_key:
            return "anthropic", AnthropicClient()
        logger.warning("anthropic_requested_but_unavailable")
    if requested == "openrouter":
        if settings.openrouter_api_key:
            return "openrouter", OpenRouterClient()
        logger.warning("openrouter_requested_but_unavailable")
    if settings.openrouter_api_key:
        return "openrouter", OpenRouterClient()
    if settings.anthropic_api_key:
        return "anthropic", AnthropicClient()
    return requested, None


def _parse_llm_response(completion: dict[str, object], symbol: str) -> IntelResponse | None:
    """Parse and validate OpenRouter completion payload into strict response."""
    content = _extract_message_content(completion)
    if content is None:
        return None
    raw_object = _extract_json_object(content)
    if raw_object is None:
        return None
    try:
        parsed = json.loads(raw_object)
    except json.JSONDecodeError:
        logger.warning("intel_json_decode_failed")
        return None
    if not isinstance(parsed, dict):
        return None

    summary = str(parsed.get("summary", "")).strip()
    if not summary:
        return None
    raw_drivers = parsed.get("key_drivers", [])
    key_drivers = _to_string_list(raw_drivers)[:6] if isinstance(raw_drivers, list) else []
    raw_bias = str(parsed.get("action_bias", "neutral")).lower()
    action_bias: Literal["bullish", "bearish", "neutral"]
    if raw_bias in {"bullish", "bearish", "neutral"}:
        action_bias = cast(Literal["bullish", "bearish", "neutral"], raw_bias)
    else:
        action_bias = "neutral"

    scenarios = _parse_scenarios(parsed.get("scenarios"))
    if not scenarios:
        return None
    return IntelResponse(
        provider="openrouter",
        model=settings.openrouter_primary_model,
        generated_at=datetime.now(timezone.utc),
        symbol=symbol,
        summary=summary,
        key_drivers=key_drivers,
        action_bias=action_bias,
        scenarios=scenarios,
        warnings=[],
    )


def _parse_scenarios(raw_scenarios: object) -> list[IntelScenario]:
    """Convert raw scenario payloads into validated scenario objects."""
    if not isinstance(raw_scenarios, list):
        return []
    parsed: list[IntelScenario] = []
    for item in raw_scenarios[:3]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip() or "Scenario"
        rationale = str(item.get("rationale", "")).strip() or "No rationale provided."
        scenario = IntelScenario(
            name=name[:80],
            probability=_clamp(_to_float(item.get("probability"), 0.33), 0.0, 1.0),
            expected_move_percent=_to_float(item.get("expected_move_percent"), 0.0),
            confidence=_clamp(_to_float(item.get("confidence"), 0.5), 0.0, 1.0),
            rationale=rationale[:500],
        )
        parsed.append(scenario)
    total_probability = sum(s.probability for s in parsed)
    if total_probability <= 0:
        return []
    return [
        IntelScenario(
            name=scenario.name,
            probability=round(scenario.probability / total_probability, 4),
            expected_move_percent=scenario.expected_move_percent,
            confidence=scenario.confidence,
            rationale=scenario.rationale,
        )
        for scenario in parsed
    ]


def _extract_message_content(completion: dict[str, object]) -> str | None:
    """Extract first completion message content from OpenRouter payload."""
    choices = completion.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content if isinstance(content, str) else None


def _extract_json_object(content: str) -> str | None:
    """Extract JSON object from plain text or fenced markdown text."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL)
    if fenced is not None:
        return fenced.group(1)
    direct = re.search(r"\{.*\}", content, flags=re.DOTALL)
    return direct.group(0) if direct is not None else None


def _to_string_list(raw_values: list[object]) -> list[str]:
    """Convert list payload to cleaned strings."""
    normalized: list[str] = []
    for value in raw_values:
        text = str(value).strip()
        if text:
            normalized.append(text[:120])
    return normalized


def _to_float(value: object, default: float) -> float:
    """Safely convert object to float."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value to inclusive range."""
    return max(minimum, min(maximum, value))


def _heuristic_intel(
    symbol: str,
    market_context: str,
    horizon_hours: int,
    risk_profile: Literal["conservative", "balanced", "aggressive"],
    warnings: list[str],
) -> IntelResponse:
    """Deterministic intelligence output when external LLM is unavailable."""
    lowered = market_context.lower()
    positive_hits = sum(
        lowered.count(keyword)
        for keyword in ("beat", "growth", "upgrade", "strong", "expansion", "surge")
    )
    negative_hits = sum(
        lowered.count(keyword)
        for keyword in ("miss", "downgrade", "lawsuit", "weak", "decline", "risk")
    )
    sentiment_score = positive_hits - negative_hits
    if sentiment_score > 1:
        action_bias: Literal["bullish", "bearish", "neutral"] = "bullish"
    elif sentiment_score < -1:
        action_bias = "bearish"
    else:
        action_bias = "neutral"

    move_scale = 0.6 if risk_profile == "conservative" else 1.4 if risk_profile == "aggressive" else 1.0
    expected_center = round(sentiment_score * 0.8 * move_scale, 2)
    base_probability = 0.45 if action_bias == "neutral" else 0.55
    adverse_probability = 0.2 if action_bias != "neutral" else 0.3
    upside_probability = 1.0 - base_probability - adverse_probability

    scenarios = [
        IntelScenario(
            name="Base Case",
            probability=round(base_probability, 4),
            expected_move_percent=expected_center,
            confidence=0.66,
            rationale=f"Primary path over the next {horizon_hours} hours from current catalysts.",
        ),
        IntelScenario(
            name="Upside Breakout",
            probability=round(upside_probability, 4),
            expected_move_percent=round(abs(expected_center) + 1.35 * move_scale, 2),
            confidence=0.58,
            rationale="Momentum continuation if positioning and liquidity align.",
        ),
        IntelScenario(
            name="Downside Shock",
            probability=round(adverse_probability, 4),
            expected_move_percent=round(-abs(expected_center) - 1.1 * move_scale, 2),
            confidence=0.54,
            rationale="Unexpected macro or idiosyncratic risk can dominate in thin liquidity windows.",
        ),
    ]
    key_drivers = _heuristic_key_drivers(lowered)
    summary = (
        f"{symbol} signal is {action_bias} with deterministic confidence layering. "
        f"Output is calibrated for {risk_profile} profile."
    )
    return IntelResponse(
        provider="heuristic-fallback",
        model=None,
        generated_at=datetime.now(timezone.utc),
        symbol=symbol,
        summary=summary,
        key_drivers=key_drivers,
        action_bias=action_bias,
        scenarios=scenarios,
        warnings=warnings,
    )


def _heuristic_key_drivers(lowered_context: str) -> list[str]:
    """Extract top context drivers from known market catalysts."""
    drivers_map: dict[str, str] = {
        "earnings": "Earnings momentum and guidance revisions",
        "guidance": "Forward guidance repricing",
        "fed": "Macro policy sensitivity",
        "inflation": "Inflation surprise transmission",
        "merger": "M&A integration and synergy pricing",
        "downgrade": "Analyst rating pressure",
        "upgrade": "Analyst sentiment upgrade flow",
        "volume": "Participation depth and flow quality",
    }
    drivers = [
        description for keyword, description in drivers_map.items() if keyword in lowered_context
    ]
    if not drivers:
        return [
            "Cross-asset risk sentiment shift",
            "Positioning imbalance and de-grossing risk",
            "Liquidity regime transition",
        ]
    return drivers[:6]
