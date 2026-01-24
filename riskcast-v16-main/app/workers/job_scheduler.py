"""
Job Scheduler
Service for enqueueing and managing risk run jobs.
"""
from __future__ import annotations

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.risk_run_job import RiskRunJob, RiskRunJobStatus
from app.models.risk_run import RiskRun, RiskRunStatus
from app.shared.exceptions import NotFoundError


class JobStatus:
    """Job status information"""
    def __init__(
        self,
        job_id: str,
        run_id: str,
        status: str,
        attempt_count: int,
        max_attempts: int,
        next_retry_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
        created_at: datetime = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        self.job_id = job_id
        self.run_id = run_id
        self.status = status
        self.attempt_count = attempt_count
        self.max_attempts = max_attempts
        self.next_retry_at = next_retry_at
        self.last_error = last_error
        self.created_at = created_at
        self.started_at = started_at
        self.completed_at = completed_at


class JobScheduler:
    """Service for scheduling and managing risk run jobs"""
    
    def __init__(self, db: Session):
        """
        Initialize job scheduler.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def enqueue_risk_run(
        self,
        run_id: str,
        priority: int = 0,
        max_attempts: int = 3
    ) -> RiskRunJob:
        """
        Enqueue a risk run for processing.
        
        Args:
            run_id: Risk run ID (UUID string)
            priority: Job priority (higher = higher priority, default: 0)
            max_attempts: Maximum retry attempts (default: 3)
            
        Returns:
            Created RiskRunJob instance
            
        Raises:
            NotFoundError: If run not found
        """
        # Verify run exists
        run = self.db.query(RiskRun).filter(RiskRun.id == run_id).first()
        if not run:
            raise NotFoundError(
                resource="risk_run",
                resource_id=run_id,
            )
        
        # Check if job already exists for this run
        existing_job = (
            self.db.query(RiskRunJob)
            .filter(RiskRunJob.run_id == run_id)
            .filter(
                RiskRunJob.status.in_([
                    RiskRunJobStatus.PENDING,
                    RiskRunJobStatus.LOCKED,
                    RiskRunJobStatus.PROCESSING
                ])
            )
            .first()
        )
        
        if existing_job:
            # Job already exists and is not completed/failed
            return existing_job
        
        # Create new job
        job = RiskRunJob(
            run_id=run_id,
            status=RiskRunJobStatus.PENDING,
            priority=priority,
            max_attempts=max_attempts,
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """
        Get status of a job.
        
        Args:
            job_id: Job ID (UUID string)
            
        Returns:
            JobStatus if found, None otherwise
        """
        job = self.db.query(RiskRunJob).filter(RiskRunJob.id == job_id).first()
        if not job:
            return None
        
        return JobStatus(
            job_id=job.id,
            run_id=job.run_id,
            status=job.status.value if hasattr(job.status, 'value') else str(job.status),
            attempt_count=job.attempt_count,
            max_attempts=job.max_attempts,
            next_retry_at=job.next_retry_at,
            last_error=job.last_error,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.
        
        Only cancels jobs that are PENDING, LOCKED, or PROCESSING.
        Completed or failed jobs cannot be cancelled.
        
        Args:
            job_id: Job ID (UUID string)
            
        Returns:
            True if job was cancelled, False if not found or cannot be cancelled
        """
        job = self.db.query(RiskRunJob).filter(RiskRunJob.id == job_id).first()
        if not job:
            return False
        
        # Only cancel if job is not completed/failed
        if job.status in [RiskRunJobStatus.COMPLETED, RiskRunJobStatus.FAILED]:
            return False
        
        # Update job status (mark as failed with no retry)
        job.status = RiskRunJobStatus.FAILED
        job.last_error = "Job cancelled by user"
        job.completed_at = datetime.utcnow()
        job.unlock()
        
        # Also update run status if it's still pending/running
        run = self.db.query(RiskRun).filter(RiskRun.id == job.run_id).first()
        if run and run.status in [RiskRunStatus.PENDING, RiskRunStatus.RUNNING]:
            run.status = RiskRunStatus.CANCELLED
            run.completed_at = datetime.utcnow()
        
        self.db.commit()
        return True
