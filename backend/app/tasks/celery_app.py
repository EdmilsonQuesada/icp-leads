from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "icp_leads",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.enrichment", "app.tasks.monitoring"],
)

celery_app.conf.beat_schedule = {
    "monitor-leads-daily": {
        "task": "app.tasks.monitoring.run_daily_monitoring",
        "schedule": crontab(hour=3, minute=0),
    },
    "process-pending-leads": {
        "task": "app.tasks.enrichment.process_pending_queue",
        "schedule": crontab(minute=0),
    },
    "revaluate-cold-leads": {
        "task": "app.tasks.monitoring.revaluate_cold_leads",
        "schedule": crontab(day_of_week=0, hour=4),
    },
}
celery_app.conf.timezone = "America/Sao_Paulo"
