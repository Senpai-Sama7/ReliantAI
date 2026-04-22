"""
Celery application configuration for asynchronous ETL execution.
"""
from celery import Celery

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "bap",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    task_store_eager_result=settings.CELERY_TASK_ALWAYS_EAGER,
)
