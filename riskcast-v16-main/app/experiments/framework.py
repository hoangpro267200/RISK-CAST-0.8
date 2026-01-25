"""
A/B Testing Framework

Features:
1. Experiment definition
2. Variant assignment
3. Metrics collection
4. Statistical analysis
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import Column, String, Integer, DateTime, Float, Index
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.logging import get_logger
from app.database import Base

try:
    from sqlalchemy.dialects.postgresql import JSONB
    JSONType = JSONB
except (ImportError, AttributeError):
    from sqlalchemy import JSON
    JSONType = JSON


logger = get_logger(__name__)


class ExperimentStatus(str, Enum):
    """Experiment status."""
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class MetricType(str, Enum):
    """Type of metric."""
    CONVERSION = "CONVERSION"  # Boolean outcome
    CONTINUOUS = "CONTINUOUS"  # Numeric value
    COUNT = "COUNT"  # Event count
    REVENUE = "REVENUE"  # Revenue value


@dataclass
class Variant:
    """Experiment variant."""
    id: str
    name: str
    weight: float  # Percentage of traffic (0-1)
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not 0 <= self.weight <= 1:
            raise ValueError("Variant weight must be between 0 and 1")


@dataclass
class Metric:
    """Metric definition for experiment."""
    name: str
    metric_type: MetricType
    primary: bool = False
    minimum_detectable_effect: Optional[float] = None  # For power analysis


@dataclass
class Experiment:
    """Experiment definition."""
    id: str
    name: str
    description: str
    hypothesis: str

    variants: List[Variant]
    metrics: List[Metric]

    status: ExperimentStatus = ExperimentStatus.DRAFT

    # Traffic allocation
    traffic_percentage: float = 1.0  # Percentage of total traffic

    # Targeting
    targeting_rules: Dict[str, Any] = field(default_factory=dict)

    # Dates
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Sample size
    min_sample_size: int = 1000

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    def validate(self):
        """Validate experiment configuration."""
        total_weight = sum(v.weight for v in self.variants)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Variant weights must sum to 1.0, got {total_weight}")

        if len(self.variants) < 2:
            raise ValueError("Experiment must have at least 2 variants")

        primary_metrics = [m for m in self.metrics if m.primary]
        if len(primary_metrics) != 1:
            raise ValueError("Experiment must have exactly 1 primary metric")

    def get_primary_metric(self) -> Metric:
        """Get the primary metric."""
        return next(m for m in self.metrics if m.primary)


class ExperimentModel(Base):
    """Database model for experiments."""
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    hypothesis = Column(String(1000))

    status = Column(String(50), default=ExperimentStatus.DRAFT.value)

    variants = Column(JSONType, nullable=False)
    metrics = Column(JSONType, nullable=False)

    traffic_percentage = Column(Float, default=1.0)
    targeting_rules = Column(JSONType, default=dict)

    start_date = Column(DateTime)
    end_date = Column(DateTime)
    min_sample_size = Column(Integer, default=1000)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(36))
    updated_at = Column(DateTime)


class ExperimentAssignmentModel(Base):
    """Database model for experiment assignments."""
    __tablename__ = "experiment_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    variant_id = Column(String(36), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    context = Column(JSONType, default=dict)

    __table_args__ = (
        Index("ix_assignment_exp_user", "experiment_id", "user_id", unique=True),
    )


class ExperimentEventModel(Base):
    """Database model for experiment events (metrics)."""
    __tablename__ = "experiment_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    variant_id = Column(String(36), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_metadata = Column(JSONType, default=dict)


async def _run_sync(coro):
    """Run sync DB code in thread when in async context."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return coro()
    return await asyncio.to_thread(coro)


class ExperimentService:
    """Service for managing experiments."""

    def __init__(self, session: Session):
        self.session = session
        self._experiments_cache: Dict[str, Experiment] = {}

    def _create_experiment_sync(self, experiment: Experiment) -> Experiment:
        experiment.validate()

        model = ExperimentModel(
            id=experiment.id,
            name=experiment.name,
            description=experiment.description,
            hypothesis=experiment.hypothesis,
            status=experiment.status.value,
            variants=[
                {"id": v.id, "name": v.name, "weight": v.weight, "config": v.config}
                for v in experiment.variants
            ],
            metrics=[
                {
                    "name": m.name,
                    "metric_type": m.metric_type.value,
                    "primary": m.primary,
                    "minimum_detectable_effect": m.minimum_detectable_effect,
                }
                for m in experiment.metrics
            ],
            traffic_percentage=experiment.traffic_percentage,
            targeting_rules=experiment.targeting_rules,
            start_date=experiment.start_date,
            end_date=experiment.end_date,
            min_sample_size=experiment.min_sample_size,
            created_at=experiment.created_at,
            created_by=experiment.created_by,
        )

        self.session.add(model)
        self.session.commit()

        logger.info(f"Experiment created: {experiment.name}", extra={"experiment_id": experiment.id})
        return experiment

    async def create_experiment(self, experiment: Experiment) -> Experiment:
        """Create a new experiment."""
        return await _run_sync(lambda: self._create_experiment_sync(experiment))

    def _get_experiment_sync(self, experiment_id: str) -> Optional[Experiment]:
        if experiment_id in self._experiments_cache:
            return self._experiments_cache[experiment_id]

        result = self.session.execute(
            select(ExperimentModel).where(ExperimentModel.id == experiment_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            return None

        experiment = _model_to_experiment(model)
        self._experiments_cache[experiment_id] = experiment
        return experiment

    async def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID."""
        return await _run_sync(lambda: self._get_experiment_sync(experiment_id))

    def _get_running_experiments_sync(self) -> List[Experiment]:
        result = self.session.execute(
            select(ExperimentModel).where(ExperimentModel.status == ExperimentStatus.RUNNING.value)
        )
        models = result.scalars().all()
        return [_model_to_experiment(m) for m in models]

    async def get_running_experiments(self) -> List[Experiment]:
        """Get all running experiments."""
        return await _run_sync(self._get_running_experiments_sync)

    def _start_experiment_sync(self, experiment_id: str):
        result = self.session.execute(
            select(ExperimentModel).where(ExperimentModel.id == experiment_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Experiment {experiment_id} not found")

        if model.status != ExperimentStatus.DRAFT.value:
            raise ValueError("Can only start experiments in DRAFT status")

        model.status = ExperimentStatus.RUNNING.value
        model.start_date = datetime.utcnow()
        model.updated_at = datetime.utcnow()

        self.session.commit()
        self._experiments_cache.pop(experiment_id, None)
        logger.info(f"Experiment started: {experiment_id}")

    async def start_experiment(self, experiment_id: str):
        """Start an experiment."""
        await _run_sync(lambda: self._start_experiment_sync(experiment_id))

    def _stop_experiment_sync(self, experiment_id: str):
        result = self.session.execute(
            select(ExperimentModel).where(ExperimentModel.id == experiment_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"Experiment {experiment_id} not found")

        model.status = ExperimentStatus.COMPLETED.value
        model.end_date = datetime.utcnow()
        model.updated_at = datetime.utcnow()

        self.session.commit()
        self._experiments_cache.pop(experiment_id, None)
        logger.info(f"Experiment stopped: {experiment_id}")

    async def stop_experiment(self, experiment_id: str):
        """Stop an experiment."""
        await _run_sync(lambda: self._stop_experiment_sync(experiment_id))

    def get_experiment_sync(self, experiment_id: str) -> Optional[Experiment]:
        """Sync get (for use from sync callers)."""
        return self._get_experiment_sync(experiment_id)

    def get_running_experiments_sync(self) -> List[Experiment]:
        """Sync get running (for use from sync callers)."""
        return self._get_running_experiments_sync()


def _model_to_experiment(model: ExperimentModel) -> Experiment:
    """Convert model to experiment."""
    return Experiment(
        id=model.id,
        name=model.name,
        description=model.description or "",
        hypothesis=model.hypothesis or "",
        status=ExperimentStatus(model.status),
        variants=[
            Variant(
                id=v["id"],
                name=v["name"],
                weight=v["weight"],
                config=v.get("config", {}),
            )
            for v in model.variants
        ],
        metrics=[
            Metric(
                name=m["name"],
                metric_type=MetricType(m["metric_type"]),
                primary=m.get("primary", False),
                minimum_detectable_effect=m.get("minimum_detectable_effect"),
            )
            for m in model.metrics
        ],
        traffic_percentage=model.traffic_percentage,
        targeting_rules=model.targeting_rules or {},
        start_date=model.start_date,
        end_date=model.end_date,
        min_sample_size=model.min_sample_size,
        created_at=model.created_at,
        created_by=model.created_by,
    )
