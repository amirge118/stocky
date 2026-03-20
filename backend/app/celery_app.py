from celery import Celery  # type: ignore[import-untyped]

from app.core.config import settings

celery_app = Celery(
    "stocky",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.alert_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    beat_schedule={
        "check-alerts-every-60s": {
            "task": "app.tasks.alert_tasks.check_alerts",
            "schedule": 60.0,
        }
    },
)
