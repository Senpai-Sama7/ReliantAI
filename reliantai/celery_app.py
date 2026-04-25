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
        "prospect_tasks.send_follow_up_message": {"queue": "outreach"},
        "prospect_tasks.process_scheduled_followups": {"queue": "outreach"},
        "prospect_tasks.process_inbound_response": {"queue": "outreach"},
        "provisioning_tasks.provision_client_site": {"queue": "provisioning"},
    },
    "beat_schedule": {
        "process-scheduled-followups": {
            "task": "prospect_tasks.process_scheduled_followups",
            "schedule": 300.0,
        },
        "weekly-gbp-posts": {
            "task": "client_tasks.generate_weekly_gbp_posts",
            "schedule": crontab(day_of_week=1, hour=9, minute=0),
        },
        "monthly-seo-report": {
            "task": "client_tasks.generate_monthly_seo_report",
            "schedule": crontab(day_of_month=1, hour=8, minute=0),
        },
    },
})

app.autodiscover_tasks(["reliantai.tasks"])
