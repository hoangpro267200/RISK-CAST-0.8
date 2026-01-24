"""
Risk Run Background Worker
Asynchronous worker for processing risk run jobs
RISKCAST V3 - Modular Monolith
"""
import asyncio
import socket
import os
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import SessionLocal, engine
from app.modules.risk_runs.models import RiskRun, RiskRunJob, RiskRunStatus, RiskRunJobStatus
from app.modules.risk_assessments.models import RiskAssessment
from app.modules.risk_engine_v3.service import RiskEngineV3
from app.modules.risk_engine_v3.schemas import RiskEngineInputV3, RiskEngineRunConfig
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.schemas import AuditContext
from app.modules.audit_ledger.models import ActorType

logger = logging.getLogger(__name__)


class RiskRunWorker:
    """
    Background worker for processing risk run jobs.
    
    Features:
    - Polls for queued jobs
    - Uses SELECT FOR UPDATE SKIP LOCKED for concurrent workers
    - Executes risk engine with deterministic settings
    - Handles retries with exponential backoff
    - Updates run status and results
    - Emits audit events
    """
    
    POLL_INTERVAL = 1  # seconds
    LOCK_TIMEOUT = 300  # 5 minutes
    MAX_ATTEMPTS = 3
    BACKOFF_BASE = 60  # seconds
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize risk run worker.
        
        Args:
            db_url: Database URL (optional, uses default from config if not provided)
        """
        self.db_url = db_url
        self.worker_id = f"{socket.gethostname()}-{os.getpid()}"
        self.running = False
        logger.info(f"RiskRunWorker initialized with worker_id={self.worker_id}")
    
    @contextmanager
    def _get_session(self):
        """
        Get database session context manager.
        
        Yields:
            SQLAlchemy session
        """
        session = SessionLocal()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    async def start(self):
        """Start the worker loop"""
        self.running = True
        logger.info(f"Worker {self.worker_id} starting")
        
        try:
            while self.running:
                try:
                    job = await self._acquire_job()
                    if job:
                        await self._process_job(job)
                    else:
                        await asyncio.sleep(self.POLL_INTERVAL)
                except KeyboardInterrupt:
                    logger.info(f"Worker {self.worker_id} received interrupt signal")
                    break
                except Exception as e:
                    logger.exception(f"Worker error: {e}")
                    await asyncio.sleep(self.POLL_INTERVAL)
        finally:
            logger.info(f"Worker {self.worker_id} stopped")
    
    async def stop(self):
        """Stop the worker"""
        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False
    
    async def _acquire_job(self) -> Optional[RiskRunJob]:
        """
        Attempt to acquire a job using SELECT FOR UPDATE SKIP LOCKED.
        
        This allows multiple workers to process jobs concurrently without
        conflicts. Each worker will get a different job.
        
        Returns:
            RiskRunJob if available, None otherwise
        """
        # Run database query in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        def _query_job():
            with self._get_session() as session:
                # Find available job
                # Note: with_for_update(skip_locked=True) requires MySQL 8.0+ or PostgreSQL
                # For older MySQL, we'll use a different approach
                try:
                    job = session.query(RiskRunJob).filter(
                        and_(
                            RiskRunJob.status == RiskRunJobStatus.QUEUED,
                            RiskRunJob.available_at <= datetime.utcnow(),
                            RiskRunJob.attempt_count < self.MAX_ATTEMPTS
                        )
                    ).with_for_update(skip_locked=True).order_by(
                        RiskRunJob.available_at.asc()
                    ).first()
                except Exception:
                    # Fallback for databases that don't support SKIP LOCKED
                    # Try to lock by updating status atomically
                    job = session.query(RiskRunJob).filter(
                        and_(
                            RiskRunJob.status == RiskRunJobStatus.QUEUED,
                            RiskRunJob.available_at <= datetime.utcnow(),
                            RiskRunJob.attempt_count < self.MAX_ATTEMPTS,
                            RiskRunJob.locked_by.is_(None)  # Not locked
                        )
                    ).order_by(RiskRunJob.available_at.asc()).first()
                
                if not job:
                    return None
                
                # Lock the job
                job.status = RiskRunJobStatus.LOCKED
                job.locked_by = self.worker_id
                job.locked_at = datetime.utcnow()
                job.attempt_count += 1
                
                session.commit()
                session.refresh(job)
                
                return job
        
        try:
            job = await loop.run_in_executor(None, _query_job)
            if job:
                logger.debug(f"Acquired job {job.id} for run {job.risk_run_id}")
            return job
        except Exception as e:
            logger.error(f"Error acquiring job: {e}")
            return None
    
    async def _process_job(self, job: RiskRunJob):
        """
        Process a single job.
        
        Steps:
        1. Load run and assessment
        2. Mark run as started
        3. Execute engine
        4. Update run with result
        5. Mark job as done
        6. Emit audit event
        
        Args:
            job: RiskRunJob to process
        """
        logger.info(f"Processing job {job.id} for run {job.risk_run_id}")
        
        run = None
        try:
            # Load run and assessment in a session
            loop = asyncio.get_event_loop()
            
            def _load_data():
                with self._get_session() as session:
                    # Load run
                    run = session.query(RiskRun).filter(
                        RiskRun.id == job.risk_run_id
                    ).first()
                    
                    if not run:
                        raise ValueError(f"Run {job.risk_run_id} not found")
                    
                    # Load assessment
                    assessment = session.query(RiskAssessment).filter(
                        RiskAssessment.id == run.risk_assessment_id
                    ).first()
                    
                    if not assessment:
                        raise ValueError(f"Assessment {run.risk_assessment_id} not found")
                    
                    # Mark run as started
                    run.status = RiskRunStatus.RUNNING
                    run.started_at = datetime.utcnow()
                    session.commit()
                    session.refresh(run)
                    
                    return run, assessment
            
            run, assessment = await loop.run_in_executor(None, _load_data)
            
            logger.info(
                f"Started run {run.id} for assessment {assessment.id} "
                f"with seed={run.seed}, iterations={run.iterations}"
            )
            
            # Execute engine (async)
            engine = RiskEngineV3()
            
            input_dto = RiskEngineInputV3(
                tenant_id=run.tenant_id,
                risk_assessment_id=run.risk_assessment_id,
                input_schema_version=assessment.input_schema_version,
                input_snapshot=assessment.input_snapshot_json,
                input_hash=assessment.input_hash,
                corridor_id=assessment.corridor_id
            )
            
            config = RiskEngineRunConfig(
                engine_version=run.engine_version,
                model_version_id=run.model_version_id,
                model_payload=None,  # TODO: Load from model_versioning in Stage 2
                result_schema_version=run.result_schema_version,
                seed=run.seed,
                seed_strategy=run.seed_strategy.value,
                iterations=run.iterations,
                options=run.options_json
            )
            
            result, result_hash = await engine.run(input_dto, config)
            
            # Update run with result
            def _update_success():
                with self._get_session() as session:
                    # Reload run to get latest state
                    run = session.query(RiskRun).filter(
                        RiskRun.id == job.risk_run_id
                    ).first()
                    
                    if not run:
                        raise ValueError(f"Run {job.risk_run_id} not found")
                    
                    # Update run with result
                    run.status = RiskRunStatus.SUCCEEDED
                    run.result_json = result.model_dump(exclude_none=True, mode='json')
                    run.result_hash = result_hash
                    run.completed_at = datetime.utcnow()
                    
                    # Mark job done
                    job_db = session.query(RiskRunJob).filter(
                        RiskRunJob.id == job.id
                    ).first()
                    if job_db:
                        job_db.status = RiskRunJobStatus.DONE
                    
                    session.commit()
                    session.refresh(run)
                    
                    return run
            
            run = await loop.run_in_executor(None, _update_success)
            
            # Emit audit event
            await self._emit_audit(run, 'risk_run.completed')
            
            logger.info(
                f"Job {job.id} completed successfully. "
                f"Run {run.id} result_hash={result_hash[:16]}..."
            )
            
        except Exception as e:
            logger.exception(f"Job {job.id} failed: {e}")
            
            # Update run as failed
            def _update_failure():
                with self._get_session() as session:
                    # Reload run
                    run = session.query(RiskRun).filter(
                        RiskRun.id == job.risk_run_id
                    ).first()
                    
                    if not run:
                        return None
                    
                    # Update run as failed
                    run.status = RiskRunStatus.FAILED
                    run.error_json = {
                        'type': type(e).__name__,
                        'message': str(e)
                    }
                    run.completed_at = datetime.utcnow()
                    
                    # Update job for retry or mark as failed
                    job_db = session.query(RiskRunJob).filter(
                        RiskRunJob.id == job.id
                    ).first()
                    
                    if job_db:
                        if job_db.attempt_count >= self.MAX_ATTEMPTS:
                            # Max attempts reached, mark as failed
                            job_db.status = RiskRunJobStatus.FAILED
                        else:
                            # Schedule retry with exponential backoff
                            job_db.status = RiskRunJobStatus.QUEUED
                            job_db.locked_by = None
                            job_db.locked_at = None
                            job_db.available_at = datetime.utcnow() + timedelta(
                                seconds=self.BACKOFF_BASE * (2 ** (job_db.attempt_count - 1))
                            )
                    
                    session.commit()
                    
                    return run
            
            loop = asyncio.get_event_loop()
            run = await loop.run_in_executor(None, _update_failure)
            
            if run:
                await self._emit_audit(run, 'risk_run.failed')
    
    async def _emit_audit(self, run: RiskRun, action: str):
        """
        Emit audit event for run action.
        
        Args:
            run: RiskRun instance
            action: Action name (e.g., 'risk_run.completed', 'risk_run.failed')
        """
        try:
            def _log_audit():
                with self._get_session() as session:
                    audit_service = AuditLedgerService(session)
                    
                    context = AuditContext(
                        request_id=None,
                        trace_id=None,
                        ip=None,
                        user_agent=f"RiskRunWorker/{self.worker_id}",
                        route=None,
                        method=None
                    )
                    
                    return audit_service, context
            
            audit_service, context = await asyncio.get_event_loop().run_in_executor(None, _log_audit)
            
            await audit_service.log_event(
                tenant_id=run.tenant_id,
                actor_type=ActorType.SYSTEM,
                actor_id=self.worker_id,
                action=action,
                resource_type='risk_run',
                resource_id=str(run.id),
                context=context
            )
        except Exception as e:
            # Log audit failure but don't fail the job processing
            logger.error(f"Failed to emit audit event for run {run.id}: {e}")
