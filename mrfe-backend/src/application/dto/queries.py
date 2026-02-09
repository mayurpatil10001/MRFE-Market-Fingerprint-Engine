"""CQRS query DTOs."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from src.application.dto.base_dto import StrictBaseModel


class GetEventByIdQuery(StrictBaseModel):
    """Query to fetch event by id."""

    event_id: str


class SearchEventsQuery(StrictBaseModel):
    """Query to search events."""

    event_type: str | None = None
    severity: str | None = None
    source: str | None = None
    is_active: bool | None = None
    query_text: str | None = None
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=200)] = 20
    sort_by: str = "detected_at"
    sort_order: str = "desc"


class GetFingerprintQuery(StrictBaseModel):
    """Query to fetch fingerprint by id."""

    fingerprint_id: str


class GetForecastQuery(StrictBaseModel):
    """Query to fetch forecast by id."""

    forecast_id: str
