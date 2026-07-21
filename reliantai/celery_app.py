import os
from celery import Celery

_redis_url = os.environ.get("REDIS_URL")
if not _redis_url:
    # Fail closed outside explicit local/test — never silently use an open Redis.
    if os.environ.get("ENVIRONMENT", "production").lower() in {"dev", "development", "local", "test"}:
        _redis_url = "redis://localhost:6379/0"
    else:
        raise RuntimeError("REDIS_URL is required")

app = Celery("reliantai")

app.config_from_object({
    "broker_url": _redis_url,
    "result_backend": _redis_url,
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
        "prospect_tasks.dispatch_queued_outreach": {"queue": "outreach"},
    },
    "beat_schedule": {
        "process-scheduled-followups": {
            "task": "prospect_tasks.process_scheduled_followups",
            "schedule": 300.0,
        },
        "dispatch-queued-outreach": {
            "task": "prospect_tasks.dispatch_queued_outreach",
            "schedule": 60.0,
        },
    },
})

app.autodiscover_tasks(["reliantai.tasks"])
