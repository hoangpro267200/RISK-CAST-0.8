"""
Celery Application Configuration
"""

import os
from celery import Celery
from kombu import Exchange, Queue

from app.config import settings


# Create Celery app
celery_app = Celery(
    "riskcast",
    broker=settings.CELERY_BROKER_URL or os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=settings.CELERY_RESULT_BACKEND or os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=[
        "app.tasks.risk_tasks",
        "app.tasks.notification_tasks",
        "app.tasks.report_tasks",
        "app.tasks.data_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_concurrency=4,
    worker_max_tasks_per_child=1000,
    
    # Result backend
    result_expires=86400,  # 24 hours
    
    # Rate limiting
    task_default_rate_limit="100/m",
    
    # Retry policy
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Routing
    task_routes={
        "app.tasks.risk_tasks.*": {"queue": "risk"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
        "app.tasks.data_tasks.*": {"queue": "data"},
    },
    
    # Queues
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("risk", Exchange("risk"), routing_key="risk.#"),
        Queue("notifications", Exchange("notifications"), routing_key="notifications.#"),
        Queue("reports", Exchange("reports"), routing_key="reports.#"),
        Queue("data", Exchange("data"), routing_key="data.#"),
    ),
    task_default_queue="default",
    
    # Beat schedule
    beat_schedule={
        "refresh-exchange-rates": {
            "task": "app.tasks.data_tasks.refresh_exchange_rates",
            "schedule": 300.0,  # Every 5 minutes
        },
        "refresh-weather-data": {
            "task": "app.tasks.data_tasks.refresh_weather_data",
            "schedule": 900.0,  # Every 15 minutes
        },
        "process-expiring-quotes": {
            "task": "app.tasks.notification_tasks.process_expiring_quotes",
            "schedule": 3600.0,  # Every hour
        },
        "generate-daily-risk-report": {
            "task": "app.tasks.report_tasks.generate_daily_risk_report",
            "schedule": {
                "hour": 6,
                "minute": 0,
            },
        },
        "cleanup-old-data": {
            "task": "app.tasks.data_tasks.cleanup_old_data",
            "schedule": 86400.0,  # Daily
        },
    },
)


# Signals
@celery_app.task(bind=True, name="app.tasks.health_check")
def health_check(self):
    """Health check task."""
    return {"status": "healthy", "task_id": self.request.id}
