"""API dependency composition root."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services import MRFEApplicationService
from src.application.use_cases import (
    DetectEventFromNewsUseCase,
    GenerateFingerprintUseCase,
    GenerateForecastUseCase,
    GetEventByIdUseCase,
    GetFingerprintUseCase,
    GetForecastUseCase,
    SearchEventsUseCase,
    UpdateFingerprintUseCase,
)
from src.infrastructure.database.session import get_db_session
from src.infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork
from src.infrastructure.ml import (
    AdvancedEnsembleForecastGenerator,
    FingerprintSimilarityService,
    MLFingerprintGenerator,
    NLPAugmentedEventDetectionService,
)


def get_application_service(session: AsyncSession = Depends(get_db_session)) -> MRFEApplicationService:
    """Build MRFE application service with injected dependencies."""
    uow = SQLAlchemyUnitOfWork(session)
    similarity_service = FingerprintSimilarityService()
    detect_uc = DetectEventFromNewsUseCase(uow=uow, detector=NLPAugmentedEventDetectionService())
    fingerprint_uc = GenerateFingerprintUseCase(
        uow=uow,
        generator=MLFingerprintGenerator(),
        similarity_service=similarity_service,
    )
    update_fingerprint_uc = UpdateFingerprintUseCase(uow=uow, similarity_service=similarity_service)
    forecast_uc = GenerateForecastUseCase(
        uow=uow,
        generator=AdvancedEnsembleForecastGenerator(similarity_service=similarity_service),
    )
    return MRFEApplicationService(
        detect_event_from_news=detect_uc,
        generate_fingerprint=fingerprint_uc,
        update_fingerprint=update_fingerprint_uc,
        generate_forecast=forecast_uc,
        get_event_by_id=GetEventByIdUseCase(uow=uow),
        search_events=SearchEventsUseCase(uow=uow),
        get_fingerprint=GetFingerprintUseCase(uow=uow),
        get_forecast=GetForecastUseCase(uow=uow),
    )
