"""Forecast API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.v1.dependencies import get_application_service
from src.api.rest.v1.schemas import (
    ForecastResponse,
    ForecastBacktestRequest,
    ForecastBacktestResponse,
    GenerateForecastRequest,
    SearchForecastsResponse,
)
from src.application.dto.commands import GenerateForecastCommand
from src.application.dto.queries import GetForecastQuery
from src.application.services import MRFEApplicationService
from src.application.use_cases.mappers import to_forecast_dto
from src.core.security import get_current_user
from src.domain.interfaces import Pagination
from src.domain.value_objects.event_id import EventId
from src.infrastructure.database.repositories import SQLAlchemyForecastRepository
from src.infrastructure.database.session import get_db_session
from src.infrastructure.ml.backtesting import backtest_metrics

router = APIRouter(prefix="/forecasts", tags=["forecasts"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ForecastResponse)
async def generate_forecast(
    payload: GenerateForecastRequest,
    service: MRFEApplicationService = Depends(get_application_service),
) -> ForecastResponse:
    """Generate forecast from event/fingerprint."""
    item = await service.handle_generate_forecast(
        GenerateForecastCommand(
            event_id=payload.event_id,
            fingerprint_id=payload.fingerprint_id,
            asset_symbol=payload.asset_symbol,
            forecast_horizon_hours=payload.forecast_horizon_hours,
            model_version=payload.model_version,
        )
    )
    return ForecastResponse.model_validate(item.model_dump())


@router.get("/{forecast_id}", response_model=ForecastResponse)
async def get_forecast(
    forecast_id: str,
    service: MRFEApplicationService = Depends(get_application_service),
) -> ForecastResponse:
    """Get forecast by id."""
    item = await service.handle_get_forecast(GetForecastQuery(forecast_id=forecast_id))
    return ForecastResponse.model_validate(item.model_dump())


@router.post("/backtest", response_model=ForecastBacktestResponse)
async def backtest_forecasts(payload: ForecastBacktestRequest) -> ForecastBacktestResponse:
    """Compute backtest metrics for forecast series."""
    metrics = backtest_metrics(payload.predictions, payload.actuals)
    return ForecastBacktestResponse.model_validate(metrics)


@router.get("", response_model=SearchForecastsResponse)
async def list_forecasts(
    event_id: str | None = Query(default=None),
    asset_symbol: str | None = Query(default=None, min_length=1, max_length=20),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
) -> SearchForecastsResponse:
    """List forecasts using event_id or asset filter with pagination."""
    repo = SQLAlchemyForecastRepository(session)
    if event_id:
        all_items = await repo.list_by_event(EventId.from_string(event_id))
        start = (page - 1) * page_size
        paged_items = all_items[start : start + page_size]
        items = [ForecastResponse.model_validate(to_forecast_dto(item).model_dump()) for item in paged_items]
        return SearchForecastsResponse(items=items, page=page, page_size=page_size, total=len(all_items))
    if asset_symbol:
        result = await repo.search_by_asset(
            asset_symbol=asset_symbol.upper(),
            pagination=Pagination(page=page, page_size=page_size),
        )
        items = [ForecastResponse.model_validate(to_forecast_dto(item).model_dump()) for item in result.items]
        return SearchForecastsResponse(
            items=items,
            page=result.page,
            page_size=result.page_size,
            total=result.total,
        )
    return SearchForecastsResponse(items=[], page=page, page_size=page_size, total=0)
