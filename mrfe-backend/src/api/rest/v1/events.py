"""Event API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.api.rest.v1.dependencies import get_application_service
from src.api.rest.v1.schemas import (
    EventClassificationRequest,
    EventResponse,
    NewsDetectionRequest,
    SearchEventsResponse,
)
from src.application.dto.commands import DetectEventFromNewsCommand
from src.application.dto.queries import GetEventByIdQuery, SearchEventsQuery
from src.application.services import MRFEApplicationService
from src.core.security import get_current_user
from src.core.utils.common import sanitize_text
from src.infrastructure.cache import RedisCacheService

router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(get_current_user)])


@router.post("/detect", response_model=list[EventResponse])
async def detect_events(
    payload: NewsDetectionRequest,
    service: MRFEApplicationService = Depends(get_application_service),
) -> list[EventResponse]:
    """Detect events from raw news input."""
    results = await service.handle_detect(
        DetectEventFromNewsCommand(
            news_content=sanitize_text(payload.news_content),
            source=sanitize_text(payload.source),
        )
    )
    return [EventResponse.model_validate(item.model_dump()) for item in results]


@router.post("/classify", response_model=EventResponse)
async def classify_event(
    payload: EventClassificationRequest,
    service: MRFEApplicationService = Depends(get_application_service),
) -> EventResponse:
    """Classify one event payload and return the top candidate."""
    synthesized_news = f"{payload.title.strip()}. {payload.description.strip()}"
    results = await service.handle_detect(
        DetectEventFromNewsCommand(
            news_content=sanitize_text(synthesized_news),
            source=sanitize_text(payload.source),
        )
    )
    top = results[0]
    return EventResponse.model_validate(top.model_dump())


@router.get("/{event_id}", response_model=EventResponse)
async def get_event_by_id(
    event_id: str,
    service: MRFEApplicationService = Depends(get_application_service),
) -> EventResponse:
    """Get one event by id."""
    cache = RedisCacheService.from_url()
    cache_key = f"event:{event_id}"
    try:
        cached = await cache.get_json(cache_key)
    except Exception:  # noqa: BLE001
        cached = None
    if cached is not None:
        return EventResponse.model_validate(cached)
    item = await service.handle_get_event(GetEventByIdQuery(event_id=event_id))
    response_model = EventResponse.model_validate(item.model_dump())
    try:
        await cache.set_json(cache_key, response_model.model_dump(mode="json"))
    except Exception:  # noqa: BLE001
        pass
    return response_model


@router.get("", response_model=SearchEventsResponse)
async def search_events(
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    source: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    query_text: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    service: MRFEApplicationService = Depends(get_application_service),
) -> SearchEventsResponse:
    """Search events."""
    result = await service.handle_search_events(
        SearchEventsQuery(
            event_type=event_type,
            severity=severity,
            source=source,
            is_active=is_active,
            query_text=query_text,
            page=page,
            page_size=page_size,
        )
    )
    return SearchEventsResponse.model_validate(result.model_dump())
