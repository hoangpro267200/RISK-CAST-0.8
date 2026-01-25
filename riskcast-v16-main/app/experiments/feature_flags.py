"""
Feature Flags System

Features:
1. Boolean flags
2. Percentage rollouts
3. User targeting
4. Flag dependencies
"""

import asyncio
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy import Column, String, Boolean, Float, DateTime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import Base
from app.core.logging import get_logger

try:
    from sqlalchemy.dialects.postgresql import JSONB
    JSONType = JSONB
except (ImportError, AttributeError):
    from sqlalchemy import JSON
    JSONType = JSON


logger = get_logger(__name__)


class FlagType(str, Enum):
    """Flag type."""
    BOOLEAN = "BOOLEAN"
    PERCENTAGE = "PERCENTAGE"
    TARGETED = "TARGETED"


@dataclass
class FeatureFlag:
    """Feature flag definition."""
    key: str
    name: str
    description: str
    flag_type: FlagType
    enabled: bool = False
    percentage: float = 0.0
    targeting_rules: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class FeatureFlagModel(Base):
    """Database model for feature flags."""
    __tablename__ = "feature_flags"

    key = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    flag_type = Column(String(50), default=FlagType.BOOLEAN.value)

    enabled = Column(Boolean, default=False)
    percentage = Column(Float, default=0.0)
    targeting_rules = Column(JSONType, default=dict)
    depends_on = Column(JSONType, default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(36))
    updated_at = Column(DateTime)


async def _run_sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return coro()
    return await asyncio.to_thread(coro)


class FeatureFlagService:
    """Service for managing feature flags."""

    def __init__(self, session: Session):
        self.session = session
        self._cache: Dict[str, FeatureFlag] = {}

    def _check_targeting(self, rules: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if user matches targeting rules."""
        for rule_key, rule_value in rules.items():
            user_value = context.get(rule_key)
            if user_value is None:
                continue
            if isinstance(rule_value, list):
                if user_value not in rule_value:
                    return False
            else:
                if user_value != rule_value:
                    return False
        return True

    def _get_flag_sync(self, key: str) -> Optional[FeatureFlag]:
        if key in self._cache:
            return self._cache[key]
        result = self.session.execute(
            select(FeatureFlagModel).where(FeatureFlagModel.key == key)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        flag = FeatureFlag(
            key=model.key,
            name=model.name,
            description=model.description or "",
            flag_type=FlagType(model.flag_type),
            enabled=model.enabled,
            percentage=model.percentage,
            targeting_rules=model.targeting_rules or {},
            depends_on=model.depends_on or [],
            created_at=model.created_at,
            created_by=model.created_by,
        )
        self._cache[key] = flag
        return flag

    def _is_enabled_sync(
        self,
        key: str,
        user_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        flag = self._get_flag_sync(key)
        if not flag:
            return False

        for dep_key in flag.depends_on:
            if not self._is_enabled_sync(dep_key, user_id, user_context):
                return False

        if flag.flag_type == FlagType.BOOLEAN:
            return flag.enabled

        if flag.flag_type == FlagType.PERCENTAGE:
            if not user_id:
                return False
            h = hashlib.sha256(f"{flag.key}:{user_id}".encode()).hexdigest()[:8]
            user_pct = (int(h, 16) % 100) / 100
            return user_pct < flag.percentage

        if flag.flag_type == FlagType.TARGETED:
            ctx = user_context or {}
            if not ctx:
                return flag.enabled
            return self._check_targeting(flag.targeting_rules, ctx)

        return False

    async def create_flag(self, flag: FeatureFlag):
        """Create a new feature flag."""

        def _create():
            model = FeatureFlagModel(
                key=flag.key,
                name=flag.name,
                description=flag.description,
                flag_type=flag.flag_type.value,
                enabled=flag.enabled,
                percentage=flag.percentage,
                targeting_rules=flag.targeting_rules,
                depends_on=flag.depends_on,
                created_at=flag.created_at,
                created_by=flag.created_by,
            )
            self.session.add(model)
            self.session.commit()
            self._cache[flag.key] = flag

        await _run_sync(_create)
        logger.info(f"Feature flag created: {flag.key}")

    async def get_flag(self, key: str) -> Optional[FeatureFlag]:
        """Get a feature flag."""
        return await _run_sync(lambda: self._get_flag_sync(key))

    async def is_enabled(
        self,
        key: str,
        user_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Check if a feature flag is enabled for a user."""
        return await _run_sync(
            lambda: self._is_enabled_sync(key, user_id, user_context)
        )

    async def update_flag(
        self,
        key: str,
        enabled: Optional[bool] = None,
        percentage: Optional[float] = None,
        targeting_rules: Optional[Dict[str, Any]] = None,
    ):
        """Update a feature flag."""

        def _update():
            result = self.session.execute(
                select(FeatureFlagModel).where(FeatureFlagModel.key == key)
            )
            model = result.scalar_one_or_none()
            if not model:
                raise ValueError(f"Flag {key} not found")
            if enabled is not None:
                model.enabled = enabled
            if percentage is not None:
                model.percentage = percentage
            if targeting_rules is not None:
                model.targeting_rules = targeting_rules
            model.updated_at = datetime.utcnow()
            self.session.commit()
            self._cache.pop(key, None)

        await _run_sync(_update)
        logger.info(f"Feature flag updated: {key}")

    async def get_all_flags(self) -> List[FeatureFlag]:
        """Get all feature flags."""

        def _all():
            result = self.session.execute(select(FeatureFlagModel))
            models = result.scalars().all()
            return [
                FeatureFlag(
                    key=m.key,
                    name=m.name,
                    description=m.description or "",
                    flag_type=FlagType(m.flag_type),
                    enabled=m.enabled,
                    percentage=m.percentage,
                    targeting_rules=m.targeting_rules or {},
                    depends_on=m.depends_on or [],
                    created_at=m.created_at,
                    created_by=m.created_by,
                )
                for m in models
            ]

        return await _run_sync(_all)


def feature_flag(
    flag_key: str,
    default: Any = None,
    fallback: Optional[Callable] = None,
):
    """
    Decorator for feature flagged functions.

    Usage:
        @feature_flag("new_pricing_algorithm", default=old_pricing)
        async def calculate_premium(data):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            flag_service = kwargs.pop("_flag_service", None)
            user_id = kwargs.pop("_user_id", None)
            user_context = kwargs.pop("_user_context", None)

            enabled = False
            if flag_service:
                enabled = await flag_service.is_enabled(
                    flag_key, user_id, user_context
                )

            if enabled:
                return await func(*args, **kwargs)
            if fallback:
                if asyncio.iscoroutinefunction(fallback):
                    return await fallback(*args, **kwargs)
                return await asyncio.to_thread(fallback, *args, **kwargs)
            return default

        return wrapper

    return decorator
