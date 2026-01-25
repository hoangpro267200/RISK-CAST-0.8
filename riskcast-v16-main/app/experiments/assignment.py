"""
Experiment Assignment

Features:
1. Deterministic assignment
2. Sticky assignments
3. Targeting rules
"""

import asyncio
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.experiments.framework import (
    Experiment,
    Variant,
    ExperimentAssignmentModel,
    ExperimentStatus,
)
from app.core.logging import get_logger


logger = get_logger(__name__)


async def _run_sync(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return coro()
    return await asyncio.to_thread(coro)


class AssignmentService:
    """Handles experiment assignment for users."""

    def __init__(self, session: Session):
        self.session = session

    def _hash_assignment(self, experiment_id: str, user_id: str) -> float:
        """Generate deterministic hash for assignment. Returns value in [0, 1]."""
        combined = f"{experiment_id}:{user_id}"
        hash_bytes = hashlib.sha256(combined.encode()).digest()
        hash_int = int.from_bytes(hash_bytes[:8], byteorder="big")
        return hash_int / (2**64)

    def _select_variant(self, experiment: Experiment, hash_value: float) -> Variant:
        """Select variant based on hash value and weights."""
        cumulative = 0.0
        for variant in experiment.variants:
            cumulative += variant.weight
            if hash_value < cumulative:
                return variant
        return experiment.variants[-1]

    def _check_targeting(
        self,
        experiment: Experiment,
        user_context: Dict[str, Any],
    ) -> bool:
        """
        Check if user matches targeting rules.

        Example rules:
            {"customer_tier": ["PREMIER", "PREFERRED"], "region": ["US", "EU"], "min_cargo_value": 100000}
        """
        rules = experiment.targeting_rules
        if not rules:
            return True

        for rule_key, rule_value in rules.items():
            user_value = user_context.get(rule_key)
            if user_value is None:
                continue

            if isinstance(rule_value, list):
                if user_value not in rule_value:
                    return False
            elif isinstance(rule_value, (int, float)):
                if rule_key.startswith("min_") and user_value < rule_value:
                    return False
                if rule_key.startswith("max_") and user_value > rule_value:
                    return False
            else:
                if user_value != rule_value:
                    return False
        return True

    def _check_traffic_allocation(
        self,
        experiment: Experiment,
        hash_value: float,
    ) -> bool:
        """Check if user falls within traffic allocation."""
        return hash_value < experiment.traffic_percentage

    def _get_existing_assignment_sync(
        self,
        experiment_id: str,
        user_id: str,
    ) -> Optional[ExperimentAssignmentModel]:
        """Get existing assignment."""
        result = self.session.execute(
            select(ExperimentAssignmentModel)
            .where(ExperimentAssignmentModel.experiment_id == experiment_id)
            .where(ExperimentAssignmentModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def _store_assignment_sync(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
        context: Dict[str, Any],
    ):
        """Store assignment in database."""
        try:
            assignment = ExperimentAssignmentModel(
                experiment_id=experiment_id,
                user_id=user_id,
                variant_id=variant_id,
                assigned_at=datetime.utcnow(),
                context=context,
            )
            self.session.add(assignment)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            # Assignment already exists (race), ignore

    def _get_assignment_sync(
        self,
        experiment: Experiment,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Variant]:
        """Sync implementation of get_assignment."""
        user_context = user_context or {}

        if experiment.status != ExperimentStatus.RUNNING:
            return None

        if not self._check_targeting(experiment, user_context):
            return None

        hash_value = self._hash_assignment(experiment.id, user_id)
        if not self._check_traffic_allocation(experiment, hash_value):
            return None

        existing = self._get_existing_assignment_sync(experiment.id, user_id)
        if existing:
            variant_id = existing.variant_id
            return next((v for v in experiment.variants if v.id == variant_id), None)

        variant = self._select_variant(experiment, hash_value)
        self._store_assignment_sync(experiment.id, user_id, variant.id, user_context)

        logger.debug(
            f"User {user_id} assigned to variant {variant.name}",
            extra={"experiment_id": experiment.id},
        )
        return variant

    async def get_assignment(
        self,
        experiment: Experiment,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Variant]:
        """
        Get experiment assignment for a user.

        Returns None if not running, user doesn't match targeting, or outside traffic allocation.
        """
        return await _run_sync(
            lambda: self._get_assignment_sync(experiment, user_id, user_context)
        )

    async def _get_existing_assignment(
        self,
        experiment_id: str,
        user_id: str,
    ) -> Optional[ExperimentAssignmentModel]:
        """Get existing assignment (for metrics/tracker)."""
        return await _run_sync(
            lambda: self._get_existing_assignment_sync(experiment_id, user_id)
        )

    def _force_assignment_sync(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
    ):
        """Force a specific assignment (for testing)."""
        existing = self._get_existing_assignment_sync(experiment_id, user_id)
        if existing:
            self.session.delete(existing)
            self.session.flush()

        assignment = ExperimentAssignmentModel(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=variant_id,
            assigned_at=datetime.utcnow(),
            context={"forced": True},
        )
        self.session.add(assignment)
        self.session.commit()

    async def force_assignment(
        self,
        experiment_id: str,
        user_id: str,
        variant_id: str,
    ):
        """Force a specific assignment (for testing)."""
        await _run_sync(
            lambda: self._force_assignment_sync(experiment_id, user_id, variant_id)
        )
