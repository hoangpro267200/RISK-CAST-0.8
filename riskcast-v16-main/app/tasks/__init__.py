"""
Celery Background Tasks

Provides async task processing for:
- Risk calculations
- Notifications
- Report generation
- Data refresh
"""

from app.tasks.celery_app import celery_app

# Import task modules to register them
from app.tasks import risk_tasks
from app.tasks import notification_tasks
from app.tasks import report_tasks
from app.tasks import data_tasks

__all__ = ["celery_app"]
