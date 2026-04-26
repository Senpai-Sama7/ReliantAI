import os
from celery import Celery
from celery.schedules import crontab

app = Celery("reliantai")

app.config_from_object({
    "broker_url": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    "result_backend": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "worker_prefetch_multiplier": 1,
    "task_routes": {
        "prospect_tasks.run_prospect_pipeline": {"queue": "agents"},
        "prospect_tasks.process_scheduled_followups": {"queue": "outreach"},
        "prospect_tasks.process_inbound_response": {"queue": "outreach"},
    },
    "beat_schedule": {
        "process-scheduled-followups": {
            "task": "prospect_tasks.process_scheduled_followups",
            "schedule": 300.0,
        },
    },
})

app.autodiscover_tasks(["reliantai.tasks"])
