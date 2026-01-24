"""
Risk Run Job Model
SQLAlchemy model for risk run job queue.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum, Index
)

from app.database import Base


class RiskRunJobStatus(str, enum.Enum):
    """Risk run job execution status"""
    PENDING = "PENDING"
    LOCKED = "LOCKED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskRunJob(Base):
    """
    Risk Run Job Model
    
    Represents a job in the queue for executing a risk run.
    Supports locking, retries, and priority-based processing.
    """
    __tablename__ = "legacy_risk_run_jobs"
    
    # Primary key (UUID)
    id = Column(
        String(36),
        primary_key=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key to risk run
    run_id = Column(
        String(36),  # UUID (matches risk_runs.id)
        ForeignKey("risk_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Status
    status = Column(
        SQLEnum(RiskRunJobStatus, native_enum=False),
        default=RiskRunJobStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Priority (higher number = higher priority)
    priority = Column(Integer, nullable=False, default=0)
    
    # Locking fields
    locked_by = Column(String(255), nullable=True, index=True)  # Worker instance ID
    locked_at = Column(DateTime, nullable=True)
    lock_expires_at = Column(DateTime, nullable=True, index=True)
    
    # Retry fields
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    next_retry_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Timing fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_risk_run_jobs_status_priority_created", "status", "priority", "created_at"),
        Index("idx_risk_run_jobs_status_next_retry", "status", "next_retry_at"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<RiskRunJob(id={self.id}, run_id={self.run_id!r}, "
            f"status={self.status.value}, priority={self.priority}, "
            f"attempt_count={self.attempt_count})>"
        )
    
    def lock(self, worker_id: str, lock_duration_seconds: int = 300) -> None:
        """
        Lock this job for processing by a worker.
        
        Args:
            worker_id: Worker instance identifier
            lock_duration_seconds: Lock duration in seconds (default: 5 minutes)
        """
        self.status = RiskRunJobStatus.LOCKED
        self.locked_by = worker_id
        self.locked_at = datetime.utcnow()
        self.lock_expires_at = datetime.utcnow() + timedelta(seconds=lock_duration_seconds)
    
    def unlock(self) -> None:
        """Unlock this job (e.g., when processing completes or fails)"""
        self.status = RiskRunJobStatus.PENDING
        self.locked_by = None
        self.locked_at = None
        self.lock_expires_at = None
    
    def start_processing(self) -> None:
        """Mark job as processing"""
        self.status = RiskRunJobStatus.PROCESSING
        if not self.started_at:
            self.started_at = datetime.utcnow()
    
    def complete(self) -> None:
        """Mark job as completed"""
        self.status = RiskRunJobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.unlock()
    
    def fail(self, error_message: str, retry: bool = True) -> None:
        """
        Mark job as failed and optionally schedule retry.
        
        Args:
            error_message: Error message
            retry: Whether to schedule a retry (if attempts remaining)
        """
        self.status = RiskRunJobStatus.FAILED
        self.last_error = error_message
        self.attempt_count += 1
        self.unlock()
        
        if retry and self.attempt_count < self.max_attempts:
            # Schedule retry (exponential backoff: 30s, 2min, 10min)
            backoff_seconds_list = [30, 120, 600]  # 30s, 2min, 10min
            attempt_index = min(self.attempt_count - 1, len(backoff_seconds_list) - 1)
            backoff_seconds = backoff_seconds_list[attempt_index]
            self.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            self.status = RiskRunJobStatus.PENDING  # Reset to pending for retry
        else:
            # No more retries
            self.completed_at = datetime.utcnow()
    
    def is_locked(self) -> bool:
        """Check if job is currently locked"""
        if self.status != RiskRunJobStatus.LOCKED:
            return False
        if not self.lock_expires_at:
            return False
        return datetime.utcnow() < self.lock_expires_at
    
    def is_expired(self) -> bool:
        """Check if lock has expired"""
        if not self.lock_expires_at:
            return False
        return datetime.utcnow() >= self.lock_expires_at
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return (
            self.status == RiskRunJobStatus.FAILED and
            self.attempt_count < self.max_attempts and
            (self.next_retry_at is None or datetime.utcnow() >= self.next_retry_at)
        )
