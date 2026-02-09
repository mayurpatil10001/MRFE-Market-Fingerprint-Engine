"""Background task endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.workers.celery_app import celery_app
from src.workers.tasks import detect_event_pipeline, retrain_from_drift, validate_shadow_model

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _to_float(value: object, default: float = 0.0) -> float:
    """Safely coerce payload value to float."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float, str)):
        try:
            return float(value)
        except ValueError:
            return default
    return default


@router.post("/detect-events")
async def enqueue_detect_events(payload: dict[str, object]) -> dict[str, str]:
    """Enqueue event detection pipeline task."""
    try:
        result = detect_event_pipeline.delay(payload)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return {"task_id": result.id}


@router.post("/retrain-from-drift")
async def enqueue_retrain_from_drift(payload: dict[str, object]) -> dict[str, str]:
    """Enqueue drift-targeted retraining task."""
    try:
        model_version = str(payload.get("model_version", "unknown"))
        drift_score = _to_float(payload.get("drift_score", 0.0))
        result = retrain_from_drift.delay(model_version, drift_score)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return {"task_id": result.id}


@router.post("/validate-shadow")
async def enqueue_validate_shadow(payload: dict[str, object]) -> dict[str, str]:
    """Enqueue shadow model validation task."""
    try:
        production_model_version = str(payload.get("production_model_version", "prod-unknown"))
        candidate_model_version = str(payload.get("candidate_model_version", "candidate-unknown"))
        result = validate_shadow_model.delay(production_model_version, candidate_model_version)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return {"task_id": result.id}


@router.get("/{task_id}")
async def get_task_status(task_id: str) -> dict[str, object]:
    """Get task state/progress/result."""
    async_result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "state": async_result.state,
        "result": async_result.result if async_result.ready() else None,
    }
