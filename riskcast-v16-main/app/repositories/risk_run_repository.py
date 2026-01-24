"""
Risk Run Repository
Data access layer for risk runs with tenant isolation.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.risk_run import RiskRun, RiskRunStatus
from app.shared.exceptions import NotFoundError


class RiskRunRepository:
    """Repository for risk run data access with tenant isolation."""

    def __init__(self, db: Session):
        """
        Initialize repository.

        Args:
            db: Database session
        """
        self.db = db

    def create(
        self,
        tenant_id: str,
        assessment_id: str,
        config: Dict[str, Any],
    ) -> RiskRun:
        """
        Create a new risk run.

        Args:
            tenant_id: Tenant ID
            assessment_id: Risk assessment ID
            config: Configuration dictionary with:
                - seed: int
                - seed_strategy: str
                - iterations: int
                - engine_version: str
                - model_version_id: Optional[str]
                - max_attempts: Optional[int] (default: 3)

        Returns:
            Created RiskRun instance
        """
        run = RiskRun(
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            status=RiskRunStatus.PENDING,
            seed=config["seed"],
            seed_strategy=config["seed_strategy"],
            iterations=config.get("iterations", 10000),
            engine_version=config["engine_version"],
            model_version_id=config.get("model_version_id"),
            max_attempts=config.get("max_attempts", 3),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, tenant_id: str, run_id: str) -> Optional[RiskRun]:
        """
        Get run by ID (tenant-scoped).

        Args:
            tenant_id: Tenant ID
            run_id: Run ID (UUID)

        Returns:
            RiskRun if found, None otherwise
        """
        return (
            self.db.query(RiskRun)
            .filter(
                and_(
                    RiskRun.id == run_id,
                    RiskRun.tenant_id == tenant_id,
                )
            )
            .first()
        )

    def update_status(
        self,
        run_id: str,
        status: RiskRunStatus,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        attempt_count: Optional[int] = None,
    ) -> RiskRun:
        """
        Update run status and timestamps.

        Args:
            run_id: Run ID
            status: New status
            started_at: Optional start timestamp
            completed_at: Optional completion timestamp
            attempt_count: Optional attempt count increment

        Returns:
            Updated RiskRun instance

        Raises:
            NotFoundError: If run not found
        """
        run = self.db.query(RiskRun).filter(RiskRun.id == run_id).first()
        if not run:
            raise NotFoundError(
                resource="risk_run",
                resource_id=run_id,
            )

        run.status = status
        if started_at is not None:
            run.started_at = started_at
        if completed_at is not None:
            run.completed_at = completed_at
        if attempt_count is not None:
            run.attempt_count = attempt_count

        self.db.commit()
        self.db.refresh(run)
        return run

    def set_result(
        self,
        run_id: str,
        result_json: Dict[str, Any],
        result_hash: str,
    ) -> RiskRun:
        """
        Set run result and hash.

        Args:
            run_id: Run ID
            result_json: Result data (JSON-serializable dict)
            result_hash: SHA256 hash of canonical result

        Returns:
            Updated RiskRun instance

        Raises:
            NotFoundError: If run not found
        """
        run = self.db.query(RiskRun).filter(RiskRun.id == run_id).first()
        if not run:
            raise NotFoundError(
                resource="risk_run",
                resource_id=run_id,
            )

        run.result_json = result_json
        run.result_hash = result_hash
        run.status = RiskRunStatus.SUCCEEDED
        run.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(run)
        return run

    def set_error(
        self,
        run_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> RiskRun:
        """
        Set run error information.

        Args:
            run_id: Run ID
            error_message: Error message
            error_details: Optional error details dictionary

        Returns:
            Updated RiskRun instance

        Raises:
            NotFoundError: If run not found
        """
        run = self.db.query(RiskRun).filter(RiskRun.id == run_id).first()
        if not run:
            raise NotFoundError(
                resource="risk_run",
                resource_id=run_id,
            )

        run.error_message = error_message
        run.error_details = error_details
        run.status = RiskRunStatus.FAILED
        run.completed_at = datetime.utcnow()
        run.attempt_count += 1

        self.db.commit()
        self.db.refresh(run)
        return run

    def list_by_assessment(
        self, tenant_id: str, assessment_id: str
    ) -> List[RiskRun]:
        """
        List runs for an assessment (tenant-scoped).

        Args:
            tenant_id: Tenant ID
            assessment_id: Assessment ID

        Returns:
            List of RiskRun instances, ordered by created_at descending
        """
        return (
            self.db.query(RiskRun)
            .filter(
                and_(
                    RiskRun.assessment_id == assessment_id,
                    RiskRun.tenant_id == tenant_id,
                )
            )
            .order_by(RiskRun.created_at.desc())
            .all()
        )

    def get_pending_runs(self, limit: int = 10) -> List[RiskRun]:
        """
        Get pending runs for worker processing.

        Returns runs with status PENDING, ordered by created_at ascending.
        Not tenant-scoped (workers can process across tenants).

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of RiskRun instances
        """
        return (
            self.db.query(RiskRun)
            .filter(RiskRun.status == RiskRunStatus.PENDING)
            .order_by(RiskRun.created_at.asc())
            .limit(limit)
            .all()
        )
