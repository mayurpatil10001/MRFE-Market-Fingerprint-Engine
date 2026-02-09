"""Development demo data seeding helpers."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.commands import GenerateFingerprintCommand, GenerateForecastCommand
from src.application.use_cases import GenerateFingerprintUseCase, GenerateForecastUseCase
from src.core.config.settings import settings
from src.core.logging import get_logger
from src.domain.entities.factories.event_factory import EventFactory
from src.domain.value_objects.confidence import Confidence
from src.domain.value_objects.event_type import EventType
from src.domain.value_objects.severity import Severity
from src.infrastructure.database.models.event_model import EventModel
from src.infrastructure.database.models.fingerprint_model import FingerprintModel
from src.infrastructure.database.models.forecast_model import ForecastModel
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.ml import (
    AdvancedEnsembleForecastGenerator,
    FingerprintSimilarityService,
    MLFingerprintGenerator,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class DemoEventSeed:
    """Seed event payload."""

    event_type: str
    severity: str
    confidence: float
    title: str
    description: str
    impact_assets: tuple[str, ...]
    market_sector: str | None = None
    country: str | None = None
    sentiment_score: float | None = None


_DEMO_EVENTS: tuple[DemoEventSeed, ...] = (
    DemoEventSeed(
        event_type="MACRO_ECONOMIC",
        severity="HIGH",
        confidence=0.82,
        title="CPI Inflation Surprise Detected",
        description="Core services inflation printed hotter than expected, lifting rate path expectations.",
        impact_assets=("SPY", "TLT", "QQQ"),
        market_sector="Macro",
        country="US",
        sentiment_score=-0.32,
    ),
    DemoEventSeed(
        event_type="GEO_POLITICAL",
        severity="CRITICAL",
        confidence=0.78,
        title="Energy Supply Shock Escalation",
        description="Geopolitical escalation triggered a sharp risk-off move and energy spike.",
        impact_assets=("XLE", "CL", "SPY"),
        market_sector="Energy",
        country="ME",
        sentiment_score=-0.58,
    ),
    DemoEventSeed(
        event_type="REGULATORY_CHANGE",
        severity="MEDIUM",
        confidence=0.7,
        title="Regulatory Guidance Shifts on Bank Capital",
        description="Updated capital buffer guidance impacts systemic banks and credit spreads.",
        impact_assets=("XLF", "SPY", "TLT"),
        market_sector="Financials",
        country="US",
        sentiment_score=0.08,
    ),
)


async def seed_demo_data(session: AsyncSession) -> bool:
    """Seed demo events/fingerprints/forecasts when database is empty or incomplete."""
    if settings.is_production:
        return False

    event_count = int((await session.execute(select(func.count(EventModel.id)))).scalar_one())
    fingerprint_count = int((await session.execute(select(func.count(FingerprintModel.id)))).scalar_one())
    forecast_count = int((await session.execute(select(func.count(ForecastModel.id)))).scalar_one())

    if event_count == 0:
        uow = SQLAlchemyUnitOfWork(session)
        async with uow:
            for seed in _DEMO_EVENTS:
                event = EventFactory.create(
                    event_type=EventType.from_string(seed.event_type),
                    severity=Severity.from_string(seed.severity),
                    confidence=Confidence(seed.confidence),
                    title=seed.title,
                    description=seed.description,
                    source="demo_seed",
                    impact_assets=seed.impact_assets,
                    market_sector=seed.market_sector,
                    country=seed.country,
                    sentiment_score=seed.sentiment_score,
                )
                await uow.events.add(event)
        logger.info("demo_events_seeded", count=len(_DEMO_EVENTS))

    if fingerprint_count > 0 and forecast_count > 0:
        return event_count == 0

    events = (
        await session.execute(
            select(EventModel).order_by(EventModel.detected_at.desc()).limit(4)
        )
    ).scalars().all()

    similarity_service = FingerprintSimilarityService()
    uow = SQLAlchemyUnitOfWork(session)
    fingerprint_uc = GenerateFingerprintUseCase(
        uow=uow,
        generator=MLFingerprintGenerator(),
        similarity_service=similarity_service,
    )
    forecast_uc = GenerateForecastUseCase(
        uow=uow,
        generator=AdvancedEnsembleForecastGenerator(similarity_service=similarity_service),
    )

    generated = 0
    for event in events:
        assets = (event.impact_assets or [])[:2]
        for asset_symbol in assets:
            existing_fp = (
                await session.execute(
                    select(FingerprintModel.fingerprint_id).where(
                        FingerprintModel.event_id == event.event_id,
                        FingerprintModel.asset_symbol == asset_symbol,
                    )
                )
            ).scalar_one_or_none()

            fingerprint_id = existing_fp
            if fingerprint_id is None:
                fingerprint = await fingerprint_uc.execute(
                    GenerateFingerprintCommand(
                        event_id=event.event_id,
                        asset_symbol=asset_symbol,
                        model_version="v1",
                    )
                )
                fingerprint_id = fingerprint.fingerprint_id
                generated += 1

            existing_forecast = (
                await session.execute(
                    select(ForecastModel.forecast_id).where(
                        ForecastModel.event_id == event.event_id,
                        ForecastModel.asset_symbol == asset_symbol,
                    )
                )
            ).scalar_one_or_none()

            if existing_forecast is None and fingerprint_id is not None:
                await forecast_uc.execute(
                    GenerateForecastCommand(
                        event_id=event.event_id,
                        fingerprint_id=fingerprint_id,
                        asset_symbol=asset_symbol,
                        forecast_horizon_hours=24,
                        model_version="v1",
                    )
                )
                generated += 1

    if generated:
        logger.info("demo_forecast_fingerprint_seeded", generated=generated)
    return generated > 0
