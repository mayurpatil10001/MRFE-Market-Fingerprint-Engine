"""API v1 router."""

from fastapi import APIRouter

from src.api.rest.v1.auth import router as auth_router
from src.api.rest.v1.events import router as events_router
from src.api.rest.v1.fingerprints import router as fingerprints_router
from src.api.rest.v1.forecasts import router as forecasts_router
from src.api.rest.v1.intel import router as intel_router
from src.api.rest.v1.ml_ops import router as ml_ops_router
from src.api.rest.v1.news import router as news_router
from src.api.rest.v1.reactions import router as reactions_router
from src.api.rest.v1.system import router as system_router
from src.api.rest.v1.tasks import router as tasks_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(events_router)
api_v1_router.include_router(fingerprints_router)
api_v1_router.include_router(forecasts_router)
api_v1_router.include_router(intel_router)
api_v1_router.include_router(ml_ops_router)
api_v1_router.include_router(news_router)
api_v1_router.include_router(reactions_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(system_router)

__all__ = ["api_v1_router"]
