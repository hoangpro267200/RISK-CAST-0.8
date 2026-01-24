"""
Risk Assessments Service
Business logic for risk assessment management with input hashing
RISKCAST V3 - Modular Monolith
"""
import hashlib
import json
from typing import List, Optional
from datetime import datetime
import logging

# Import TenantScopedSession
# Note: In FastAPI context, this will be injected via dependency
# For type hints, we use TYPE_CHECKING to avoid import issues
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type checking only - actual import happens at runtime
    from app.database import TenantScopedSession
else:
    # Runtime import - try both locations
    try:
        from app.database import TenantScopedSession
    except ImportError:
        # If app.database is a package, try importing from the module file
        # This is a workaround for the package vs module conflict
        import sys
        import importlib.util
        import pathlib
        
        current_file = pathlib.Path(__file__)
        app_dir = current_file.parent.parent.parent
        db_module_path = app_dir / 'database.py'
        
        if db_module_path.exists():
            # Add parent to path temporarily
            sys.path.insert(0, str(app_dir.parent))
            try:
                from app.database import TenantScopedSession
            except ImportError:
                # Last resort: use Any type
                TenantScopedSession = None  # Will be set at runtime
        else:
            TenantScopedSession = None  # Will be set at runtime
from app.modules.risk_assessments.models import RiskAssessment, AssessmentStatus
from app.modules.risk_assessments.schemas import RiskAssessmentCreate, RiskAssessmentInputV3
from app.modules.risk_assessments.exceptions import (
    AssessmentNotFoundError,
    AssessmentValidationError,
    DuplicateAssessmentError
)
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.schemas import AuditContext
from app.modules.audit_ledger.models import ActorType

logger = logging.getLogger(__name__)


class RiskAssessmentService:
    """
    Service for risk assessment management.
    
    Handles:
    - Input validation and normalization
    - Input hashing for deduplication
    - Assessment creation and retrieval
    - Audit event logging
    """
    
    INPUT_SCHEMA_VERSION = "risk_input_v3.0"
    
    def __init__(self, db: 'TenantScopedSession'):
        """
        Initialize risk assessment service.
        
        Args:
            db: Tenant-scoped database session
        """
        self.db = db
        # Audit service needs raw session, not tenant-scoped
        self.audit = AuditLedgerService(db._raw_session)
        logger.debug(f"RiskAssessmentService initialized for tenant_id={db.tenant_id}")
    
    def _canonicalize_input(self, input_data: dict) -> str:
        """
        Canonical JSON serialization for input hashing.
        
        Ensures stable key ordering, consistent numeric formatting,
        and no whitespace for reproducible hashing.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Canonical JSON string
        """
        return json.dumps(
            input_data,
            sort_keys=True,
            separators=(',', ':'),
            default=str
        )
    
    def _compute_input_hash(self, canonical_input: str) -> str:
        """
        Compute SHA256 hash of canonical input.
        
        Args:
            canonical_input: Canonical JSON string
            
        Returns:
            SHA256 hex digest
        """
        return hashlib.sha256(canonical_input.encode('utf-8')).hexdigest()
    
    async def create_assessment(
        self,
        data: RiskAssessmentCreate,
        user_id: str,
        context: AuditContext
    ) -> RiskAssessment:
        """
        Create a new risk assessment.
        
        Steps:
        1. Validate input against schema
        2. Canonicalize and hash input
        3. Check for duplicates (optional - can be enabled)
        4. Store assessment
        5. Emit audit event
        
        Args:
            data: Risk assessment creation data
            user_id: User ID creating the assessment
            context: Audit context for logging
            
        Returns:
            Created RiskAssessment instance
            
        Raises:
            AssessmentValidationError: If input validation fails
            DuplicateAssessmentError: If duplicate assessment exists (if checking enabled)
        """
        try:
            # Validate and normalize input
            # input_data is already a RiskAssessmentInputV3 instance
            input_dict = data.input_data.model_dump(exclude_none=True, mode='json')
            
            # Canonicalize input for hashing
            canonical_input = self._canonicalize_input(input_dict)
            input_hash = self._compute_input_hash(canonical_input)
            
            # Optional: Check for duplicate assessments (same input hash)
            # Uncomment if you want to prevent duplicates
            # existing = self.db.query(RiskAssessment).filter(
            #     RiskAssessment.input_hash == input_hash
            # ).first()
            # if existing:
            #     raise DuplicateAssessmentError(input_hash, existing.id)
            
            # Create assessment
            assessment = RiskAssessment(
                tenant_id=self.db.tenant_id,  # Auto-set by TenantScopedSession
                created_by_user_id=user_id,
                status=AssessmentStatus.READY,
                input_schema_version=self.INPUT_SCHEMA_VERSION,
                input_snapshot_json=input_dict,
                input_hash=input_hash,
                shipment_id=data.shipment_id,
                corridor_id=data.corridor_id
            )
            
            self.db.add(assessment)
            self.db.commit()
            self.db.refresh(assessment)
            
            logger.info(
                f"Created risk assessment {assessment.id} for tenant {self.db.tenant_id} "
                f"with input_hash {input_hash[:16]}..."
            )
            
            # Emit audit event
            try:
                await self.audit.log_event(
                    tenant_id=self.db.tenant_id,
                    actor_type='USER',
                    actor_id=str(user_id),
                    action='risk_assessment.created',
                    resource_type='risk_assessment',
                    resource_id=str(assessment.id),
                    context=context
                )
            except Exception as e:
                # Log audit failure but don't fail the assessment creation
                logger.error(f"Failed to log audit event for assessment {assessment.id}: {e}")
            
            return assessment
            
        except DuplicateAssessmentError:
            raise
        except Exception as e:
            logger.error(f"Failed to create risk assessment: {e}")
            raise AssessmentValidationError(f"Failed to create assessment: {str(e)}")
    
    async def get_assessment(self, assessment_id: str) -> RiskAssessment:
        """
        Get assessment by ID (tenant-scoped automatically).
        
        The query is automatically filtered by tenant_id due to TenantScopedSession.
        
        Args:
            assessment_id: Assessment ID (ULID)
            
        Returns:
            RiskAssessment instance
            
        Raises:
            AssessmentNotFoundError: If assessment not found or not accessible
        """
        assessment = self.db.query(RiskAssessment).filter(
            RiskAssessment.id == assessment_id
        ).first()
        
        if not assessment:
            raise AssessmentNotFoundError(assessment_id)
        
        logger.debug(f"Retrieved assessment {assessment_id} for tenant {self.db.tenant_id}")
        return assessment
    
    async def list_assessments(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[RiskAssessment]:
        """
        List assessments for tenant.
        
        Automatically filtered by tenant_id due to TenantScopedSession.
        
        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Optional status filter (DRAFT, READY, ARCHIVED)
            
        Returns:
            List of RiskAssessment instances
        """
        query = self.db.query(RiskAssessment).order_by(
            RiskAssessment.created_at.desc()
        )
        
        if status:
            # Validate status
            try:
                status_enum = AssessmentStatus(status.upper())
                query = query.filter(RiskAssessment.status == status_enum)
            except ValueError:
                raise AssessmentValidationError(
                    f"Invalid status: {status}. Must be one of: DRAFT, READY, ARCHIVED"
                )
        
        assessments = query.offset(skip).limit(limit).all()
        
        logger.debug(
            f"Listed {len(assessments)} assessments for tenant {self.db.tenant_id} "
            f"(skip={skip}, limit={limit}, status={status})"
        )
        
        return assessments
    
    async def update_assessment_status(
        self,
        assessment_id: str,
        new_status: str,
        user_id: str,
        context: AuditContext
    ) -> RiskAssessment:
        """
        Update assessment status.
        
        Args:
            assessment_id: Assessment ID
            new_status: New status (DRAFT, READY, ARCHIVED)
            user_id: User ID making the change
            context: Audit context
            
        Returns:
            Updated RiskAssessment instance
            
        Raises:
            AssessmentNotFoundError: If assessment not found
            AssessmentValidationError: If status is invalid
        """
        assessment = await self.get_assessment(assessment_id)
        
        # Validate status
        try:
            status_enum = AssessmentStatus(new_status.upper())
        except ValueError:
            raise AssessmentValidationError(
                f"Invalid status: {new_status}. Must be one of: DRAFT, READY, ARCHIVED"
            )
        
        old_status = assessment.status
        assessment.status = status_enum
        self.db.commit()
        self.db.refresh(assessment)
        
        logger.info(
            f"Updated assessment {assessment_id} status from {old_status} to {status_enum} "
            f"by user {user_id}"
        )
        
        # Emit audit event
        try:
            await self.audit.log_event(
                tenant_id=self.db.tenant_id,
                actor_type=ActorType.USER,
                actor_id=str(user_id),
                action='risk_assessment.status_updated',
                resource_type='risk_assessment',
                resource_id=str(assessment.id),
                context=context,
                diff={
                    'status': {
                        'old': str(old_status),
                        'new': str(status_enum)
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to log audit event for status update: {e}")
        
        return assessment
    
    async def archive_assessment(
        self,
        assessment_id: str,
        user_id: str,
        context: AuditContext
    ) -> RiskAssessment:
        """
        Archive an assessment (convenience method).
        
        Args:
            assessment_id: Assessment ID
            user_id: User ID archiving the assessment
            context: Audit context
            
        Returns:
            Archived RiskAssessment instance
        """
        return await self.update_assessment_status(
            assessment_id,
            AssessmentStatus.ARCHIVED.value,
            user_id,
            context
        )
    
    def find_by_input_hash(self, input_hash: str) -> Optional[RiskAssessment]:
        """
        Find assessment by input hash (for deduplication).
        
        Args:
            input_hash: SHA256 hash of input data
            
        Returns:
            RiskAssessment if found, None otherwise
        """
        return self.db.query(RiskAssessment).filter(
            RiskAssessment.input_hash == input_hash
        ).first()
