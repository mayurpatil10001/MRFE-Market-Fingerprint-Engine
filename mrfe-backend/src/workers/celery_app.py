"""Celery application configuration."""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from src.core.config.settings import settings

celery_app = Celery(
    "mrfe",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_acks_late=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=5,
    task_routes={
        "src.workers.tasks.detect_event_pipeline": {"queue": "events", "priority": 9},
        "src.workers.tasks.generate_fingerprint_batch": {"queue": "fingerprints", "priority": 8},
        "src.workers.tasks.generate_forecast_batch": {"queue": "forecasts", "priority": 8},
        "src.workers.tasks.data_backfill": {"queue": "maintenance", "priority": 3},
        "src.workers.tasks.retrain_models": {"queue": "maintenance", "priority": 2},
        "src.workers.tasks.retrain_from_drift": {"queue": "maintenance", "priority": 1},
        "src.workers.tasks.validate_shadow_model": {"queue": "maintenance", "priority": 4},
    },
    task_default_queue="default",
    beat_schedule={
        "mrfe-collect-daily-data": {
            "task": "src.workers.tasks.collect_daily_data",
            "schedule": crontab(hour=settings.data_collection_cron_hour, minute=0),
        },
        "mrfe-data-retention-cleanup": {
            "task": "src.workers.tasks.data_retention_cleanup",
            "schedule": crontab(hour=(settings.data_collection_cron_hour + 1) % 24, minute=0),
        },
    },
)
