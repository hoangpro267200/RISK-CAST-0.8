"""
Model Registry

Manages:
1. Model versions
2. Model metadata
3. Model lifecycle
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.mysql import JSON

from app.core.logging import get_logger
from app.database import Base


logger = get_logger(__name__)

# Optional Redis import
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class ModelStatus(str, Enum):
    """Model lifecycle status."""
    TRAINING = "TRAINING"
    VALIDATING = "VALIDATING"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


@dataclass
class ModelMetadata:
    """Model metadata."""
    model_name: str
    model_version: str
    
    # Status
    status: ModelStatus
    
    # Training info
    trained_at: datetime
    training_duration_seconds: float
    training_data_size: int
    
    # Performance metrics from training
    training_metrics: Dict[str, float]
    validation_metrics: Dict[str, float]
    
    # Feature info
    features: List[str]
    feature_importance: Dict[str, float]
    
    # Hyperparameters
    hyperparameters: Dict[str, Any]
    
    # Deployment info
    deployed_at: Optional[datetime] = None
    deployed_by: Optional[str] = None
    
    # Drift info
    last_drift_check: Optional[datetime] = None
    drift_score: Optional[float] = None
    
    # Metadata
    description: str = ""
    tags: List[str] = field(default_factory=list)


class ModelVersionModel(Base):
    """Database model for model versions."""
    __tablename__ = "model_versions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    
    status = Column(String(50), default=ModelStatus.TRAINING.value)
    
    trained_at = Column(DateTime)
    training_duration_seconds = Column(Float)
    training_data_size = Column(Integer)
    
    # Use JSON for MySQL, JSONB for PostgreSQL
    try:
        training_metrics = Column(JSONB, default={})
        validation_metrics = Column(JSONB, default={})
        features = Column(JSONB, default=[])
        feature_importance = Column(JSONB, default={})
        hyperparameters = Column(JSONB, default={})
        tags = Column(JSONB, default=[])
    except:
        # Fallback to JSON for MySQL
        training_metrics = Column(JSON, default={})
        validation_metrics = Column(JSON, default={})
        features = Column(JSON, default=[])
        feature_importance = Column(JSON, default={})
        hyperparameters = Column(JSON, default={})
        tags = Column(JSON, default=[])
    
    deployed_at = Column(DateTime)
    deployed_by = Column(String(36))
    
    last_drift_check = Column(DateTime)
    drift_score = Column(Float)
    
    description = Column(String(1000))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_model_name_version', 'model_name', 'model_version', unique=True),
    )


class ModelRegistry:
    """
    Model registry for version management.
    """
    
    def __init__(
        self,
        session,  # SQLAlchemy Session (sync)
        redis_client: Optional[Any] = None  # redis.Redis type
    ):
        self.session = session
        self.redis = redis_client
    
    def register_model(
        self,
        metadata: ModelMetadata
    ) -> str:
        """Register a new model version."""
        model = ModelVersionModel(
            model_name=metadata.model_name,
            model_version=metadata.model_version,
            status=metadata.status.value,
            trained_at=metadata.trained_at,
            training_duration_seconds=metadata.training_duration_seconds,
            training_data_size=metadata.training_data_size,
            training_metrics=metadata.training_metrics,
            validation_metrics=metadata.validation_metrics,
            features=metadata.features,
            feature_importance=metadata.feature_importance,
            hyperparameters=metadata.hyperparameters,
            description=metadata.description,
            tags=metadata.tags
        )
        
        self.session.add(model)
        self.session.commit()
        
        logger.info(
            f"Model registered: {metadata.model_name} v{metadata.model_version}"
        )
        
        return f"{metadata.model_name}:{metadata.model_version}"
    
    def get_model(
        self,
        model_name: str,
        version: Optional[str] = None
    ) -> Optional[ModelMetadata]:
        """Get model metadata."""
        from sqlalchemy import select
        
        query = select(ModelVersionModel).where(
            ModelVersionModel.model_name == model_name
        )
        
        if version:
            query = query.where(ModelVersionModel.model_version == version)
        else:
            # Get latest production version
            query = query.where(
                ModelVersionModel.status == ModelStatus.PRODUCTION.value
            ).order_by(ModelVersionModel.deployed_at.desc())
        
        result = self.session.execute(query)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._model_to_metadata(model)
    
    def promote_to_production(
        self,
        model_name: str,
        version: str,
        deployed_by: str
    ):
        """Promote a model to production."""
        from sqlalchemy import select
        
        # Demote current production
        result = self.session.execute(
            select(ModelVersionModel)
            .where(ModelVersionModel.model_name == model_name)
            .where(ModelVersionModel.status == ModelStatus.PRODUCTION.value)
        )
        current_prod = result.scalar_one_or_none()
        
        if current_prod:
            current_prod.status = ModelStatus.DEPRECATED.value
            current_prod.updated_at = datetime.utcnow()
        
        # Promote new version
        result = self.session.execute(
            select(ModelVersionModel)
            .where(ModelVersionModel.model_name == model_name)
            .where(ModelVersionModel.model_version == version)
        )
        new_prod = result.scalar_one_or_none()
        
        if not new_prod:
            raise ValueError(f"Model {model_name} v{version} not found")
        
        new_prod.status = ModelStatus.PRODUCTION.value
        new_prod.deployed_at = datetime.utcnow()
        new_prod.deployed_by = deployed_by
        new_prod.updated_at = datetime.utcnow()
        
        self.session.commit()
        
        # Update cache (async Redis - would need async context)
        # For now, skip Redis cache update in sync context
        # Can be called separately in async context if needed
        if self.redis:
            logger.debug(f"Redis cache update skipped (sync context): {model_name}:{version}")
        
        logger.info(f"Model promoted to production: {model_name} v{version}")
    
    def update_drift_score(
        self,
        model_name: str,
        version: str,
        drift_score: float
    ):
        """Update drift score for a model."""
        from sqlalchemy import select
        
        result = self.session.execute(
            select(ModelVersionModel)
            .where(ModelVersionModel.model_name == model_name)
            .where(ModelVersionModel.model_version == version)
        )
        model = result.scalar_one_or_none()
        
        if model:
            model.drift_score = drift_score
            model.last_drift_check = datetime.utcnow()
            model.updated_at = datetime.utcnow()
            self.session.commit()
    
    def list_models(
        self,
        status: Optional[ModelStatus] = None
    ) -> List[ModelMetadata]:
        """List all models."""
        from sqlalchemy import select
        
        query = select(ModelVersionModel)
        
        if status:
            query = query.where(ModelVersionModel.status == status.value)
        
        query = query.order_by(
            ModelVersionModel.model_name,
            ModelVersionModel.trained_at.desc()
        )
        
        result = self.session.execute(query)
        models = result.scalars().all()
        
        return [self._model_to_metadata(m) for m in models]
    
    def _model_to_metadata(self, model: ModelVersionModel) -> ModelMetadata:
        return ModelMetadata(
            model_name=model.model_name,
            model_version=model.model_version,
            status=ModelStatus(model.status),
            trained_at=model.trained_at,
            training_duration_seconds=model.training_duration_seconds,
            training_data_size=model.training_data_size,
            training_metrics=model.training_metrics or {},
            validation_metrics=model.validation_metrics or {},
            features=model.features or [],
            feature_importance=model.feature_importance or {},
            hyperparameters=model.hyperparameters or {},
            deployed_at=model.deployed_at,
            deployed_by=model.deployed_by,
            last_drift_check=model.last_drift_check,
            drift_score=model.drift_score,
            description=model.description or "",
            tags=model.tags or []
        )
