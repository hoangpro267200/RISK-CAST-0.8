"""
Experiment Metrics Collection

Features:
1. Event tracking
2. Conversion tracking
3. Revenue tracking
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.experiments.framework import (
    ExperimentEventModel,
    Metric,
    MetricType,
    Experiment,
)
from app.core.logging import get_logger


logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.experiments.assignment import AssignmentService
    from app.experiments.framework import ExperimentService


async def _run_sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return coro()
    return await asyncio.to_thread(coro)


class MetricsCollector:
    """Collects metrics for experiments."""

    def __init__(self, session: Session):
        self.session = session

    def _track_event_sync(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        event = ExperimentEventModel(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=variant_id,
            metric_name=metric_name,
            value=value,
            timestamp=datetime.utcnow(),
            event_metadata=metadata or {},
        )
        self.session.add(event)
        self.session.commit()
        logger.debug(
            f"Tracked metric {metric_name}={value}",
            extra={"experiment_id": experiment_id, "user_id": user_id},
        )

    async def track_event(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a metric event."""
        await _run_sync(
            lambda: self._track_event_sync(
                experiment_id, user_id, variant_id, metric_name, value, metadata
            )
        )

    async def track_conversion(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
        metric_name: str,
        converted: bool,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a conversion event."""
        await self.track_event(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=variant_id,
            metric_name=metric_name,
            value=1.0 if converted else 0.0,
            metadata=metadata,
        )

    async def track_revenue(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
        metric_name: str,
        revenue: Decimal,
        currency: str = "USD",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a revenue event."""
        meta = metadata or {}
        meta["currency"] = currency
        await self.track_event(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=variant_id,
            metric_name=metric_name,
            value=float(revenue),
            metadata=meta,
        )

    async def track_count(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
        metric_name: str,
        count: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a count event."""
        await self.track_event(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=variant_id,
            metric_name=metric_name,
            value=float(count),
            metadata=metadata,
        )


class ExperimentTracker:
    """High-level tracker for experiment metrics."""

    def __init__(
        self,
        session: Session,
        assignment_service: "AssignmentService",
        experiment_service: "ExperimentService",
    ):
        self.session = session
        self.assignment_service = assignment_service
        self.experiment_service = experiment_service
        self.metrics_collector = MetricsCollector(session)

    async def track(
        self,
        user_id: str,
        metric_name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a metric for all experiments the user is in."""
        experiments = await self.experiment_service.get_running_experiments()

        for experiment in experiments:
            metric_names = [m.name for m in experiment.metrics]
            if metric_name not in metric_names:
                continue

            assignment = await self.assignment_service._get_existing_assignment(
                experiment.id, user_id
            )

            if assignment:
                await self.metrics_collector.track_event(
                    experiment_id=experiment.id,
                    user_id=user_id,
                    variant_id=assignment.variant_id,
                    metric_name=metric_name,
                    value=value,
                    metadata=metadata,
                )
