"""Fingerprint API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.rest.v1.dependencies import get_application_service
from src.api.rest.v1.schemas import (
    FingerprintResponse,
    GenerateFingerprintRequest,
    SearchFingerprintsResponse,
    UpdateFingerprintRequest,
)
from src.application.dto.commands import GenerateFingerprintCommand, UpdateFingerprintCommand
from src.application.dto.queries import GetFingerprintQuery
from src.application.services import MRFEApplicationService
from src.application.use_cases.mappers import to_fingerprint_dto
from src.core.security import get_current_user, require_role
from src.domain.interfaces import Pagination
from src.domain.value_objects.event_id import EventId
from src.infrastructure.database.repositories import SQLAlchemyFingerprintRepository
from src.infrastructure.database.session import get_db_session

router = APIRouter(prefix="/fingerprints", tags=["fingerprints"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=FingerprintResponse, dependencies=[Depends(require_role("trader"))])
async def generate_fingerprint(
    payload: GenerateFingerprintRequest,
    service: MRFEApplicationService = Depends(get_application_service),
) -> FingerprintResponse:
    """Generate fingerprint from event + asset."""
    item = await service.handle_generate_fingerprint(
        GenerateFingerprintCommand(
            event_id=payload.event_id,
            asset_symbol=payload.asset_symbol,
            model_version=payload.model_version,
        )
    )
    return FingerprintResponse.model_validate(item.model_dump())


@router.patch("/{fingerprint_id}", response_model=FingerprintResponse)
async def update_fingerprint(
    fingerprint_id: str,
    payload: UpdateFingerprintRequest,
    service: MRFEApplicationService = Depends(get_application_service),
) -> FingerprintResponse:
    """Update mutable fingerprint fields."""
    item = await service.handle_update_fingerprint(
        UpdateFingerprintCommand(
            fingerprint_id=fingerprint_id,
            reaction_intensity=payload.reaction_intensity,
            volatility_impact=payload.volatility_impact,
            volume_impact=payload.volume_impact,
        )
    )
    return FingerprintResponse.model_validate(item.model_dump())


@router.get("/{fingerprint_id}", response_model=FingerprintResponse)
async def get_fingerprint(
    fingerprint_id: str,
    service: MRFEApplicationService = Depends(get_application_service),
) -> FingerprintResponse:
    """Get fingerprint by id."""
    item = await service.handle_get_fingerprint(GetFingerprintQuery(fingerprint_id=fingerprint_id))
    return FingerprintResponse.model_validate(item.model_dump())


@router.get("", response_model=SearchFingerprintsResponse)
async def list_fingerprints(
    event_id: str | None = Query(default=None),
    asset_symbol: str | None = Query(default=None, min_length=1, max_length=20),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
) -> SearchFingerprintsResponse:
    """List fingerprints using event_id or asset filter with pagination."""
    repo = SQLAlchemyFingerprintRepository(session)
    if event_id:
        all_items = await repo.list_by_event(EventId.from_string(event_id))
        start = (page - 1) * page_size
        paged_items = all_items[start : start + page_size]
        items = [FingerprintResponse.model_validate(to_fingerprint_dto(item).model_dump()) for item in paged_items]
        return SearchFingerprintsResponse(items=items, page=page, page_size=page_size, total=len(all_items))
    if asset_symbol:
        result = await repo.search_by_asset(
            asset_symbol=asset_symbol.upper(),
            pagination=Pagination(page=page, page_size=page_size),
        )
        items = [FingerprintResponse.model_validate(to_fingerprint_dto(item).model_dump()) for item in result.items]
        return SearchFingerprintsResponse(
            items=items,
            page=result.page,
            page_size=result.page_size,
            total=result.total,
        )
    return SearchFingerprintsResponse(items=[], page=page, page_size=page_size, total=0)
