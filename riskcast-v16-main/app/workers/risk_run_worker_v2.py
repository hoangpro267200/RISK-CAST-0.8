"""
Risk Run Worker V2
Async job worker for processing risk runs with locking and retry support.
"""
from __future__ import annotations

import asyncio
import socket
import os
from datetime import datetime, timedelta
from typing import Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import SessionLocal
from app.models.risk_run_job import RiskRunJob, RiskRunJobStatus
from app.models.risk_run import RiskRun, RiskRunStatus
from app.models.risk_assessment import RiskAssessment
from app.services.risk_run_service import RiskRunService
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class RiskRunWorker:
    """
    Async job worker for processing risk runs.
    
    Features:
    - Acquires jobs using SELECT FOR UPDATE SKIP LOCKED
    - Processes jobs asynchronously
    - Handles retries with exponential backoff (30s, 2min, 10min)
    - Lock expiration prevents stuck jobs
    """
    
    # Exponential backoff: 30s, 2min (120s), 10min (600s)
    BACKOFF_SECONDS = [30, 120, 600]
    DEFAULT_LOCK_DURATION = 300  # 5 minutes
    
    def __init__(self, worker_id: Optional[str] = None, poll_interval: int = 5):
        """
        Initialize worker.
        
        Args:
            worker_id: Worker instance ID (auto-generated if not provided)
            poll_interval: Poll interval in seconds when no jobs available
        """
        self.worker_id = worker_id or f"{socket.gethostname()}-{os.getpid()}"
        self.poll_interval = poll_interval
        self.running = False
        logger.info(f"RiskRunWorker initialized: worker_id={self.worker_id}")
    
    async def start(self):
        """
        Start the worker loop.
        
        Continuously polls for jobs and processes them.
        """
        self.running = True
        logger.info(f"Worker {self.worker_id} starting")
        
        try:
            while self.running:
                try:
                    job = await self.acquire_job()
                    if job:
                        await self.process_job(job)
                    else:
                        await asyncio.sleep(self.poll_interval)
                except KeyboardInterrupt:
                    logger.info(f"Worker {self.worker_id} received interrupt signal")
                    break
                except Exception as e:
                    logger.exception(f"Worker error: {e}")
                    await asyncio.sleep(self.poll_interval)
        finally:
            logger.info(f"Worker {self.worker_id} stopped")
    
    async def stop(self):
        """Stop the worker gracefully"""
        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False
    
    async def acquire_job(self) -> Optional[RiskRunJob]:
        """
        Acquire a job using SELECT FOR UPDATE SKIP LOCKED.
        
        Looks for:
        - PENDING jobs
        - Failed jobs ready for retry (next_retry_at <= now)
        - Expired locks (lock_expires_at < now)
        
        Returns:
            RiskRunJob if acquired, None otherwise
        """
        loop = asyncio.get_event_loop()
        
        def _acquire():
            db = SessionLocal()
            try:
                now = datetime.utcnow()
                
                # Find available job:
                # 1. PENDING status
                # 2. Or FAILED with retry ready (next_retry_at <= now)
                # 3. Or LOCKED with expired lock (lock_expires_at < now)
                job = (
                    db.query(RiskRunJob)
                    .filter(
                        or_(
                            # PENDING jobs
                            and_(
                                RiskRunJob.status == RiskRunJobStatus.PENDING,
                                RiskRunJob.attempt_count < RiskRunJob.max_attempts
                            ),
                            # FAILED jobs ready for retry
                            and_(
                                RiskRunJob.status == RiskRunJobStatus.FAILED,
                                RiskRunJob.attempt_count < RiskRunJob.max_attempts,
                                RiskRunJob.next_retry_at <= now
                            ),
                            # Expired locks
                            and_(
                                RiskRunJob.status == RiskRunJobStatus.LOCKED,
                                RiskRunJob.lock_expires_at < now
                            )
                        )
                    )
                    .order_by(
                        RiskRunJob.priority.desc(),  # Higher priority first
                        RiskRunJob.created_at.asc()  # Older jobs first
                    )
                    .with_for_update(skip_locked=True)  # Skip already locked rows
                    .first()
                )
                
                if not job:
                    return None
                
                # Lock the job
                job.lock(self.worker_id, lock_duration_seconds=self.DEFAULT_LOCK_DURATION)
                job.status = RiskRunJobStatus.LOCKED
                
                db.commit()
                db.refresh(job)
                
                logger.info(f"Acquired job {job.id} for run {job.run_id}")
                return job
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error acquiring job: {e}")
                return None
            finally:
                db.close()
        
        return await loop.run_in_executor(None, _acquire)
    
    async def process_job(self, job: RiskRunJob):
        """
        Process a single job.
        
        Steps:
        1. Load run and assessment
        2. Update run status to RUNNING
        3. Execute risk engine
        4. Store results
        5. Mark job COMPLETED
        
        On failure:
        - Handle failure
        - Increment attempt_count
        - Set next_retry_at with exponential backoff
        - Mark job FAILED (or PENDING for retry)
        
        Args:
            job: RiskRunJob to process
        """
        logger.info(f"Processing job {job.id} for run {job.run_id}")
        
        db = SessionLocal()
        try:
            # Load run
            run = db.query(RiskRun).filter(RiskRun.id == job.run_id).first()
            if not run:
                raise ValueError(f"Run {job.run_id} not found")
            
            # Load assessment
            assessment = db.query(RiskAssessment).filter(
                RiskAssessment.id == run.assessment_id
            ).first()
            if not assessment:
                raise ValueError(f"Assessment {run.assessment_id} not found")
            
            # Update run status to RUNNING
            run_service = RiskRunService(db, audit=AuditLedger(db))
            run = run_service.repository.update_status(
                run_id=run.id,
                status=RiskRunStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            
            # Mark job as PROCESSING
            job.start_processing()
            db.commit()
            db.refresh(job)
            
            logger.info(
                f"Started processing run {run.id} "
                f"(seed={run.seed}, iterations={run.iterations})"
            )
            
            # Execute risk engine
            try:
                completed_run = run_service.execute_run(run.id)
                
                # Mark job as COMPLETED
                job.complete()
                db.commit()
                
                logger.info(
                    f"Job {job.id} completed successfully. "
                    f"Run {run.id} result_hash={completed_run.result_hash[:16] if completed_run.result_hash else 'N/A'}..."
                )
                
            except Exception as e:
                # Handle failure
                error_message = str(e)
                logger.exception(f"Job {job.id} failed: {error_message}")
                
                # Calculate backoff based on attempt_count
                attempt_index = min(job.attempt_count, len(self.BACKOFF_SECONDS) - 1)
                backoff_seconds = self.BACKOFF_SECONDS[attempt_index]
                
                # Mark job as failed with retry
                retry = job.attempt_count < job.max_attempts
                job.fail(error_message, retry=retry)
                
                if retry:
                    # Set next_retry_at with exponential backoff
                    job.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
                    logger.info(
                        f"Job {job.id} scheduled for retry in {backoff_seconds}s "
                        f"(attempt {job.attempt_count + 1}/{job.max_attempts})"
                    )
                else:
                    logger.warning(
                        f"Job {job.id} failed after {job.attempt_count} attempts. "
                        f"Max attempts reached."
                    )
                
                db.commit()
                raise
        
        except Exception as e:
            db.rollback()
            # Job failure already handled above
            raise
        finally:
            db.close()
