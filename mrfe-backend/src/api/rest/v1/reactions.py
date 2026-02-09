"""Reaction measurement endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.v1.schemas import (
    MeasureReactionRequest,
    MeasureReactionResponse,
    ReactionAnalysisRequest,
    ReactionAnalysisResponse,
    ReactionHorizonResponse,
)
from src.core.security import get_current_user
from src.infrastructure.database.models.reaction_model import ReactionModel
from src.infrastructure.database.session import get_db_session
from src.infrastructure.ml.reaction_analyzer import ReactionAnalyzer, ReactionObservation

router = APIRouter(prefix="/reactions", tags=["reactions"], dependencies=[Depends(get_current_user)])


@router.post("/measure", response_model=MeasureReactionResponse)
async def measure_reaction(payload: MeasureReactionRequest) -> MeasureReactionResponse:
    """Compute normalized reaction metrics from pre/post event observations."""
    price_return_pct = ((payload.post_event_price - payload.pre_event_price) / payload.pre_event_price) * 100
    volume_delta_pct = ((payload.post_event_volume - payload.pre_event_volume) / payload.pre_event_volume) * 100
    if payload.pre_event_volatility <= 0:
        volatility_delta_pct = 0.0 if payload.post_event_volatility <= 0 else 100.0
    else:
        volatility_delta_pct = (
            (payload.post_event_volatility - payload.pre_event_volatility) / payload.pre_event_volatility
        ) * 100

    # Blend absolute return/volume/volatility shifts into one bounded [0, 1] intensity score.
    normalized_return = min(1.0, abs(price_return_pct) / 10.0)
    normalized_volume = min(1.0, abs(volume_delta_pct) / 200.0)
    normalized_vol = min(1.0, abs(volatility_delta_pct) / 150.0)
    reaction_intensity = round((normalized_return * 0.5) + (normalized_volume * 0.3) + (normalized_vol * 0.2), 4)

    response = MeasureReactionResponse(
        event_id=payload.event_id,
        asset_symbol=payload.asset_symbol.upper(),
        horizon_minutes=payload.horizon_minutes,
        price_return_pct=round(price_return_pct, 4),
        volume_delta_pct=round(volume_delta_pct, 4),
        volatility_delta_pct=round(volatility_delta_pct, 4),
        reaction_intensity=reaction_intensity,
        measured_at=datetime.now(timezone.utc),
    )
    return response


@router.post("/measure-and-store", response_model=MeasureReactionResponse)
async def measure_and_store_reaction(
    payload: MeasureReactionRequest,
    session: AsyncSession = Depends(get_db_session),
) -> MeasureReactionResponse:
    """Compute reaction metrics and persist them."""
    response = await measure_reaction(payload)
    record = ReactionModel(
        reaction_id=str(uuid4()),
        event_id=response.event_id,
        asset_symbol=response.asset_symbol,
        horizon_minutes=response.horizon_minutes,
        price_return_pct=response.price_return_pct,
        volume_delta_pct=response.volume_delta_pct,
        volatility_delta_pct=response.volatility_delta_pct,
        reaction_intensity=response.reaction_intensity,
        measured_at=response.measured_at,
    )
    session.add(record)
    await session.commit()
    return response


@router.post("/analyze", response_model=ReactionAnalysisResponse)
async def analyze_reaction(
    payload: ReactionAnalysisRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ReactionAnalysisResponse:
    """Analyze reaction time series and persist horizon measurements."""
    horizons = tuple(payload.horizons_minutes) if payload.horizons_minutes else None
    analyzer = ReactionAnalyzer(horizons_minutes=horizons or (1, 5, 15, 30, 60, 240, 1440))
    observations = [
        ReactionObservation(
            timestamp=item.timestamp,
            price=item.price,
            volume=item.volume,
            spread_bps=item.spread_bps,
        )
        for item in payload.observations
    ]
    result = analyzer.analyze(
        event_id=payload.event_id,
        asset_symbol=payload.asset_symbol,
        event_time=payload.event_time,
        observations=observations,
    )
    for horizon in result.horizons:
        session.add(
            ReactionModel(
                reaction_id=str(uuid4()),
                event_id=result.event_id,
                asset_symbol=result.asset_symbol,
                horizon_minutes=horizon.horizon_minutes,
                price_return_pct=horizon.price_return_pct,
                volume_delta_pct=horizon.volume_delta_pct,
                volatility_delta_pct=horizon.volatility_delta_pct,
                reaction_intensity=horizon.reaction_intensity,
                measured_at=result.measured_at,
            )
        )
    await session.commit()
    return ReactionAnalysisResponse(
        event_id=result.event_id,
        asset_symbol=result.asset_symbol,
        measured_at=result.measured_at,
        baseline_price=result.baseline_price,
        baseline_volume=result.baseline_volume,
        baseline_volatility=result.baseline_volatility,
        horizons=[
            ReactionHorizonResponse(
                horizon_minutes=item.horizon_minutes,
                price_return_pct=item.price_return_pct,
                volume_delta_pct=item.volume_delta_pct,
                volatility_delta_pct=item.volatility_delta_pct,
                spread_delta_bps=item.spread_delta_bps,
                reaction_intensity=item.reaction_intensity,
            )
            for item in result.horizons
        ],
        quality=result.quality,
    )


@router.get("", response_model=list[MeasureReactionResponse])
async def list_reactions(
    asset_symbol: str | None = Query(default=None, min_length=1, max_length=20),
    event_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
) -> list[MeasureReactionResponse]:
    """List measured reactions with optional filters."""
    stmt = select(ReactionModel).order_by(desc(ReactionModel.measured_at)).limit(limit)
    if asset_symbol:
        stmt = stmt.where(ReactionModel.asset_symbol == asset_symbol.upper())
    if event_id:
        stmt = stmt.where(ReactionModel.event_id == event_id)
    records = (await session.execute(stmt)).scalars().all()
    return [
        MeasureReactionResponse(
            event_id=record.event_id,
            asset_symbol=record.asset_symbol,
            horizon_minutes=record.horizon_minutes,
            price_return_pct=record.price_return_pct,
            volume_delta_pct=record.volume_delta_pct,
            volatility_delta_pct=record.volatility_delta_pct,
            reaction_intensity=record.reaction_intensity,
            measured_at=record.measured_at,
        )
        for record in records
    ]
