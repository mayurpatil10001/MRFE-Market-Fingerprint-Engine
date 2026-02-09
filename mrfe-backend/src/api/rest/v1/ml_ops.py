"""MLOps endpoints for model lifecycle and drift intelligence."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.rest.v1.schemas import (
    DriftCheckRequest,
    DriftCheckResponse,
    IncrementalUpdateRequest,
    IncrementalUpdateResponse,
    ModelRecordResponse,
    ModelRegistrationRequest,
    PromoteModelRequest,
    RegimeDetectRequest,
    RegimeDetectResponse,
    RetrainingScheduleResponse,
)
from src.core.config.settings import settings
from src.core.logging import get_logger
from src.core.monitoring.metrics import ml_drift_alert_total, ml_registry_updates_total
from src.core.security import get_current_user, require_role
from src.infrastructure.ml import (
    IncrementalLearner,
    ModelRegistryService,
    PopulationDriftDetector,
    RegimeDetector,
    RetrainingScheduler,
)
from src.workers.tasks import retrain_from_drift

logger = get_logger(__name__)
router = APIRouter(prefix="/ml", tags=["ml-ops"], dependencies=[Depends(get_current_user)])
registry_service = ModelRegistryService()
drift_detector = PopulationDriftDetector()
incremental_learner = IncrementalLearner(dimension=8)
regime_detector = RegimeDetector()
retraining_scheduler = RetrainingScheduler(interval_hours=24)


@router.get("/models", response_model=list[ModelRecordResponse])
async def list_models() -> list[ModelRecordResponse]:
    """List all registered models."""
    records = await registry_service.list_models()
    return [
        ModelRecordResponse(
            model_id=record.model_id,
            name=record.name,
            version=record.version,
            framework=record.framework,
            artifact_uri=record.artifact_uri,
            stage=record.stage,
            created_at=record.created_at,
            tags=record.tags,
        )
        for record in records
    ]


@router.post(
    "/models/register",
    response_model=ModelRecordResponse,
    dependencies=[Depends(require_role("trader"))],
)
async def register_model(payload: ModelRegistrationRequest) -> ModelRecordResponse:
    """Register a model candidate in staging."""
    record = await registry_service.register_model(
        name=payload.name,
        version=payload.version,
        framework=payload.framework,
        artifact_uri=payload.artifact_uri,
        tags=payload.tags,
    )
    ml_registry_updates_total.labels(action="register").inc()
    return ModelRecordResponse(
        model_id=record.model_id,
        name=record.name,
        version=record.version,
        framework=record.framework,
        artifact_uri=record.artifact_uri,
        stage=record.stage,
        created_at=record.created_at,
        tags=record.tags,
    )


@router.post(
    "/models/{model_id}/promote",
    response_model=ModelRecordResponse,
    dependencies=[Depends(require_role("trader"))],
)
async def promote_model(model_id: str, payload: PromoteModelRequest) -> ModelRecordResponse:
    """Promote a model to target stage."""
    record = await registry_service.promote_model(model_id=model_id, stage=payload.stage)
    ml_registry_updates_total.labels(action="promote").inc()
    return ModelRecordResponse(
        model_id=record.model_id,
        name=record.name,
        version=record.version,
        framework=record.framework,
        artifact_uri=record.artifact_uri,
        stage=record.stage,
        created_at=record.created_at,
        tags=record.tags,
    )


@router.post(
    "/drift/check",
    response_model=DriftCheckResponse,
    dependencies=[Depends(require_role("trader"))],
)
async def check_drift(payload: DriftCheckRequest) -> DriftCheckResponse:
    """Compute drift score and optionally trigger retraining."""
    report = drift_detector.evaluate(
        baseline_distribution=payload.baseline_distribution,
        live_distribution=payload.live_distribution,
        alert_threshold=settings.drift_alert_threshold,
    )
    task_id: str | None = None
    retrain_queued = False
    if report.status == "drift_alert":
        ml_drift_alert_total.labels(model_version=payload.model_version, status=report.status).inc()
        try:
            result = retrain_from_drift.delay(payload.model_version, report.drift_score)
            task_id = result.id
            retrain_queued = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("drift_retrain_enqueue_failed", error=str(exc))
    return DriftCheckResponse(
        drift_score=report.drift_score,
        status=report.status,
        threshold=settings.drift_alert_threshold,
        retrain_queued=retrain_queued,
        task_id=task_id,
        baseline_entropy=report.baseline_entropy,
        live_entropy=report.live_entropy,
    )


@router.post(
    "/learning/incremental-update",
    response_model=IncrementalUpdateResponse,
    dependencies=[Depends(require_role("trader"))],
)
async def incremental_update(payload: IncrementalUpdateRequest) -> IncrementalUpdateResponse:
    """Update online learner centroid with one vector observation."""
    centroid = incremental_learner.update(payload.vector)
    return IncrementalUpdateResponse(
        observations=incremental_learner.observations,
        centroid=centroid,
        updated_at=incremental_learner.last_updated,
    )


@router.post(
    "/regime/detect",
    response_model=RegimeDetectResponse,
    dependencies=[Depends(require_role("trader"))],
)
async def detect_regime(payload: RegimeDetectRequest) -> RegimeDetectResponse:
    """Detect current market regime from a return series."""
    result = regime_detector.detect(payload.returns)
    return RegimeDetectResponse(
        regime=result.regime,
        volatility_score=result.volatility_score,
        trend_score=result.trend_score,
        detected_at=result.detected_at,
    )


@router.get(
    "/retraining/schedule",
    response_model=RetrainingScheduleResponse,
    dependencies=[Depends(require_role("trader"))],
)
async def get_retraining_schedule() -> RetrainingScheduleResponse:
    """Expose retraining due state for automation hooks."""
    due = retraining_scheduler.due()
    if due:
        retraining_scheduler.mark_run()
    return RetrainingScheduleResponse(
        due=due,
        interval_hours=24,
        last_run=retraining_scheduler.last_run,
    )
