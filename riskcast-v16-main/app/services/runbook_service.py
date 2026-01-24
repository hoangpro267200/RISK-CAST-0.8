"""
Runbook management service.

Manages operational runbooks and their executions.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.models.runbook import Runbook, RunbookExecution
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class RunbookService:
    """Service for managing operational runbooks."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize runbook service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_runbook(
        self,
        runbook_id: str,
        title: str,
        category: str,
        steps: List[Dict[str, Any]],
        created_by: str,
        description: Optional[str] = None,
        severity_level: Optional[str] = None,
        trigger_conditions: Optional[str] = None,
        prerequisites: Optional[Dict[str, Any]] = None,
        rollback_steps: Optional[List[Dict[str, Any]]] = None,
        escalation_path: Optional[Dict[str, Any]] = None,
        estimated_duration_minutes: Optional[int] = None,
        owner_user_id: Optional[str] = None,
        reviewer_user_id: Optional[str] = None
    ) -> Runbook:
        """
        Create a new runbook.
        
        Args:
            runbook_id: Unique runbook identifier
            title: Runbook title
            category: Category (INCIDENT_RESPONSE, DISASTER_RECOVERY, etc.)
            steps: List of step dictionaries
            created_by: User ID creating (ULID string)
            ... other optional fields
            
        Returns:
            Created Runbook instance
            
        Raises:
            RunbookExistsError: If runbook_id already exists
        """
        # Check if runbook_id already exists
        existing = self.db.query(Runbook).filter(
            Runbook.runbook_id == runbook_id
        ).first()
        if existing:
            raise RunbookExistsError(f"Runbook with ID {runbook_id} already exists")
        
        # Validate steps
        if not steps or len(steps) == 0:
            raise InvalidRunbookError("Runbook must have at least one step")
        
        # Ensure step numbers are sequential
        for i, step in enumerate(steps, start=1):
            if 'step_number' not in step:
                step['step_number'] = i
        
        runbook = Runbook(
            id=generate_ulid(),
            runbook_id=runbook_id,
            title=title,
            description=description,
            category=category,
            severity_level=severity_level,
            trigger_conditions=trigger_conditions,
            prerequisites_json=prerequisites,
            steps_json=steps,
            rollback_steps_json=rollback_steps,
            escalation_path_json=escalation_path,
            estimated_duration_minutes=estimated_duration_minutes,
            status='DRAFT',
            version=1,
            owner_user_id=owner_user_id or created_by,
            reviewer_user_id=reviewer_user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(runbook)
        self.db.commit()
        self.db.refresh(runbook)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="RUNBOOK",
            action="CREATED",
            entity_type="runbook",
            entity_id=runbook.id,
            actor_type="USER",
            actor_id=created_by,
            payload={"runbook_id": runbook_id, "title": title, "category": category}
        )
        
        logger.info(f"Created runbook: {runbook.id} ({runbook_id})")
        
        return runbook
    
    def get_runbook(self, runbook_id: str) -> Runbook:
        """
        Get runbook by ID.
        
        Args:
            runbook_id: Runbook ID (ULID string)
            
        Returns:
            Runbook instance
            
        Raises:
            RunbookNotFoundError: If runbook not found
        """
        return self._get_runbook(runbook_id)
    
    def publish_runbook(
        self,
        runbook_id: str,
        published_by: str
    ) -> Runbook:
        """
        Publish a runbook.
        
        Args:
            runbook_id: Runbook ID (ULID string)
            published_by: User ID publishing (ULID string)
            
        Returns:
            Updated Runbook instance
            
        Raises:
            RunbookNotFoundError: If runbook not found
            InvalidRunbookStateError: If runbook is not in DRAFT status
            InvalidRunbookError: If runbook doesn't have required fields
        """
        runbook = self._get_runbook(runbook_id)
        
        if runbook.status != 'DRAFT':
            raise InvalidRunbookStateError(f"Runbook is {runbook.status}, cannot publish")
        
        # Validate has required fields
        if not runbook.steps_json or len(runbook.steps_json) == 0:
            raise InvalidRunbookError("Runbook must have at least one step")
        
        runbook.status = 'PUBLISHED'
        runbook.published_at = datetime.utcnow()
        runbook.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(runbook)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="RUNBOOK",
            action="PUBLISHED",
            entity_type="runbook",
            entity_id=runbook_id,
            actor_type="USER",
            actor_id=published_by,
            payload={"runbook_id": runbook.runbook_id, "version": runbook.version}
        )
        
        logger.info(f"Published runbook: {runbook_id}")
        
        return runbook
    
    def list_runbooks(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        severity_level: Optional[str] = None
    ) -> List[Runbook]:
        """
        List runbooks with filters.
        
        Args:
            category: Filter by category
            status: Filter by status
            severity_level: Filter by severity level
            
        Returns:
            List of Runbook instances
        """
        query = self.db.query(Runbook)
        
        if category:
            query = query.filter(Runbook.category == category)
        if status:
            query = query.filter(Runbook.status == status)
        if severity_level:
            query = query.filter(Runbook.severity_level == severity_level)
        
        return query.order_by(Runbook.category, Runbook.runbook_id).all()
    
    def get_runbooks_by_category(
        self,
        category: str,
        status: str = 'PUBLISHED'
    ) -> List[Runbook]:
        """
        Get runbooks by category.
        
        Args:
            category: Category name
            status: Status filter (default: PUBLISHED)
            
        Returns:
            List of Runbook instances
        """
        return self.db.query(Runbook).filter(
            Runbook.category == category,
            Runbook.status == status
        ).order_by(Runbook.runbook_id).all()
    
    # ==================== Executions ====================
    
    def start_execution(
        self,
        runbook_id: str,
        executed_by: str,
        execution_type: str = 'INCIDENT',
        incident_reference: Optional[str] = None
    ) -> RunbookExecution:
        """
        Start a runbook execution.
        
        Args:
            runbook_id: Runbook ID (ULID string)
            executed_by: User ID executing (ULID string)
            execution_type: Execution type (INCIDENT, TEST, MAINTENANCE)
            incident_reference: Optional incident reference
            
        Returns:
            Created RunbookExecution instance
            
        Raises:
            RunbookNotFoundError: If runbook not found
            InvalidRunbookStateError: If runbook is not PUBLISHED
        """
        runbook = self._get_runbook(runbook_id)
        
        if runbook.status != 'PUBLISHED':
            raise InvalidRunbookStateError("Can only execute PUBLISHED runbooks")
        
        execution = RunbookExecution(
            id=generate_ulid(),
            runbook_id=runbook_id,
            execution_type=execution_type,
            incident_reference=incident_reference,
            status='IN_PROGRESS',
            executed_by_user_id=executed_by,
            current_step=1,
            step_results_json=[],
            started_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="RUNBOOK_EXECUTION",
            action="STARTED",
            entity_type="runbook_execution",
            entity_id=execution.id,
            actor_type="USER",
            actor_id=executed_by,
            payload={
                "runbook_id": runbook.runbook_id,
                "runbook_title": runbook.title,
                "execution_type": execution_type,
                "incident_reference": incident_reference
            }
        )
        
        logger.info(f"Started runbook execution: {execution.id} for runbook {runbook_id}")
        
        return execution
    
    def complete_step(
        self,
        execution_id: str,
        step_number: int,
        status: str,
        completed_by: str,
        notes: Optional[str] = None
    ) -> RunbookExecution:
        """
        Complete a step in the execution.
        
        Args:
            execution_id: Execution ID (ULID string)
            step_number: Step number completed
            status: Step status (COMPLETED, FAILED, SKIPPED)
            completed_by: User ID completing (ULID string)
            notes: Optional notes
            
        Returns:
            Updated RunbookExecution instance
            
        Raises:
            ExecutionNotFoundError: If execution not found
            InvalidExecutionStateError: If execution is not IN_PROGRESS
        """
        execution = self._get_execution(execution_id)
        
        if execution.status != 'IN_PROGRESS':
            raise InvalidExecutionStateError(f"Execution is {execution.status}, cannot update steps")
        
        # Record step result
        step_result = {
            "step": step_number,
            "status": status,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "completed_by": completed_by,
            "notes": notes
        }
        
        results = execution.step_results_json or []
        # Update existing result if step already recorded, otherwise append
        existing_index = next((i for i, r in enumerate(results) if r.get('step') == step_number), None)
        if existing_index is not None:
            results[existing_index] = step_result
        else:
            results.append(step_result)
        
        execution.step_results_json = results
        
        # Move to next step if completed successfully
        runbook = self._get_runbook(execution.runbook_id)
        total_steps = len(runbook.steps_json)
        
        if status == 'COMPLETED' and step_number < total_steps:
            execution.current_step = step_number + 1
        elif status == 'FAILED':
            # Don't advance if step failed
            pass
        
        self.db.commit()
        self.db.refresh(execution)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="RUNBOOK_EXECUTION",
            action="STEP_COMPLETED",
            entity_type="runbook_execution",
            entity_id=execution_id,
            actor_type="USER",
            actor_id=completed_by,
            payload={
                "step_number": step_number,
                "status": status,
                "current_step": execution.current_step
            }
        )
        
        logger.info(f"Completed step {step_number} in execution {execution_id}: {status}")
        
        return execution
    
    def complete_execution(
        self,
        execution_id: str,
        success: bool,
        completed_by: str,
        lessons_learned: Optional[str] = None,
        deviations: Optional[List[str]] = None
    ) -> RunbookExecution:
        """
        Complete a runbook execution.
        
        Args:
            execution_id: Execution ID (ULID string)
            success: Whether execution was successful
            completed_by: User ID completing (ULID string)
            lessons_learned: Optional lessons learned
            deviations: Optional list of deviations from runbook
            
        Returns:
            Updated RunbookExecution instance
            
        Raises:
            ExecutionNotFoundError: If execution not found
        """
        execution = self._get_execution(execution_id)
        
        duration = (datetime.utcnow() - execution.started_at).total_seconds() / 60
        
        execution.status = 'COMPLETED' if success else 'FAILED'
        execution.completed_at = datetime.utcnow()
        execution.outcome_json = {
            "success": success,
            "duration_minutes": round(duration, 2),
            "deviations": deviations or [],
            "lessons_learned": lessons_learned
        }
        
        self.db.commit()
        self.db.refresh(execution)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="RUNBOOK_EXECUTION",
            action="COMPLETED",
            entity_type="runbook_execution",
            entity_id=execution_id,
            actor_type="USER",
            actor_id=completed_by,
            payload={
                "success": success,
                "duration_minutes": round(duration, 2),
                "total_steps": len(execution.step_results_json or [])
            }
        )
        
        logger.info(f"Completed runbook execution: {execution_id} (success: {success})")
        
        return execution
    
    def abort_execution(
        self,
        execution_id: str,
        aborted_by: str,
        reason: Optional[str] = None
    ) -> RunbookExecution:
        """
        Abort a runbook execution.
        
        Args:
            execution_id: Execution ID (ULID string)
            aborted_by: User ID aborting (ULID string)
            reason: Optional reason for abort
            
        Returns:
            Updated RunbookExecution instance
            
        Raises:
            ExecutionNotFoundError: If execution not found
        """
        execution = self._get_execution(execution_id)
        
        if execution.status != 'IN_PROGRESS':
            raise InvalidExecutionStateError(f"Execution is {execution.status}, cannot abort")
        
        execution.status = 'ABORTED'
        execution.completed_at = datetime.utcnow()
        
        if reason:
            outcome = execution.outcome_json or {}
            outcome['abort_reason'] = reason
            execution.outcome_json = outcome
        
        self.db.commit()
        self.db.refresh(execution)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="RUNBOOK_EXECUTION",
            action="ABORTED",
            entity_type="runbook_execution",
            entity_id=execution_id,
            actor_type="USER",
            actor_id=aborted_by,
            payload={"reason": reason}
        )
        
        logger.warning(f"Aborted runbook execution: {execution_id}")
        
        return execution
    
    def get_execution(self, execution_id: str) -> RunbookExecution:
        """
        Get execution by ID.
        
        Args:
            execution_id: Execution ID (ULID string)
            
        Returns:
            RunbookExecution instance
            
        Raises:
            ExecutionNotFoundError: If execution not found
        """
        return self._get_execution(execution_id)
    
    def get_execution_history(
        self,
        runbook_id: str,
        limit: int = 10
    ) -> List[RunbookExecution]:
        """
        Get execution history for a runbook.
        
        Args:
            runbook_id: Runbook ID (ULID string)
            limit: Maximum number of executions to return
            
        Returns:
            List of RunbookExecution instances (ordered by started_at desc)
        """
        return self.db.query(RunbookExecution).filter(
            RunbookExecution.runbook_id == runbook_id
        ).order_by(
            RunbookExecution.started_at.desc()
        ).limit(limit).all()
    
    def get_active_executions(
        self,
        execution_type: Optional[str] = None
    ) -> List[RunbookExecution]:
        """
        Get active (in-progress) executions.
        
        Args:
            execution_type: Optional execution type filter
            
        Returns:
            List of active RunbookExecution instances
        """
        query = self.db.query(RunbookExecution).filter(
            RunbookExecution.status == 'IN_PROGRESS'
        )
        
        if execution_type:
            query = query.filter(RunbookExecution.execution_type == execution_type)
        
        return query.order_by(RunbookExecution.started_at).all()
    
    # ==================== Private Methods ====================
    
    def _get_runbook(self, runbook_id: str) -> Runbook:
        """
        Get runbook by ID.
        
        Args:
            runbook_id: Runbook ID (ULID string)
            
        Returns:
            Runbook instance
            
        Raises:
            RunbookNotFoundError: If runbook not found
        """
        runbook = self.db.query(Runbook).filter(
            Runbook.id == runbook_id
        ).first()
        if not runbook:
            raise RunbookNotFoundError(f"Runbook {runbook_id} not found")
        return runbook
    
    def _get_execution(self, execution_id: str) -> RunbookExecution:
        """
        Get execution by ID.
        
        Args:
            execution_id: Execution ID (ULID string)
            
        Returns:
            RunbookExecution instance
            
        Raises:
            ExecutionNotFoundError: If execution not found
        """
        execution = self.db.query(RunbookExecution).filter(
            RunbookExecution.id == execution_id
        ).first()
        if not execution:
            raise ExecutionNotFoundError(f"Execution {execution_id} not found")
        return execution


# Exception classes
class RunbookNotFoundError(Exception):
    """Runbook not found"""
    pass


class RunbookExistsError(Exception):
    """Runbook already exists"""
    pass


class InvalidRunbookStateError(Exception):
    """Invalid runbook state for operation"""
    pass


class InvalidRunbookError(Exception):
    """Invalid runbook configuration"""
    pass


class ExecutionNotFoundError(Exception):
    """Runbook execution not found"""
    pass


class InvalidExecutionStateError(Exception):
    """Invalid execution state for operation"""
    pass
