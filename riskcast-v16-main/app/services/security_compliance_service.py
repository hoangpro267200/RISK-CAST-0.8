"""
Security compliance service.

Manages security controls, assessments, and remediation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.security import SecurityControl, ControlAssessment, ControlRemediationPlan
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class SecurityComplianceService:
    """Service for security compliance management."""
    
    # Standard control frameworks
    FRAMEWORKS = ['SOC2', 'ISO27001', 'GDPR', 'PCI_DSS', 'NIST']
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize security compliance service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    # ==================== Control Management ====================
    
    def create_control(
        self,
        control_id: str,
        name: str,
        framework: str,
        created_by: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        control_type: Optional[str] = None,
        implementation_type: Optional[str] = None,
        evidence_requirements: Optional[Dict[str, Any]] = None,
        owner_user_id: Optional[str] = None,
        owner_role: Optional[str] = None
    ) -> SecurityControl:
        """
        Create a new security control.
        
        Args:
            control_id: Unique control identifier
            name: Control name
            framework: Framework (SOC2, ISO27001, GDPR, PCI_DSS, NIST)
            created_by: User ID creating (ULID string)
            ... other optional fields
            
        Returns:
            Created SecurityControl instance
            
        Raises:
            InvalidFrameworkError: If framework is not valid
        """
        if framework not in self.FRAMEWORKS:
            raise InvalidFrameworkError(f"Framework must be one of {self.FRAMEWORKS}")
        
        # Check if control_id already exists
        existing = self.db.query(SecurityControl).filter(
            SecurityControl.control_id == control_id
        ).first()
        if existing:
            raise ControlExistsError(f"Control with ID {control_id} already exists")
        
        control = SecurityControl(
            id=generate_ulid(),
            control_id=control_id,
            name=name,
            description=description,
            framework=framework,
            category=category,
            subcategory=subcategory,
            control_type=control_type,
            implementation_type=implementation_type,
            evidence_requirements_json=evidence_requirements,
            owner_user_id=owner_user_id,
            owner_role=owner_role,
            status='NOT_IMPLEMENTED',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(control)
        self.db.commit()
        self.db.refresh(control)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="SECURITY_CONTROL",
            action="CREATED",
            entity_type="security_control",
            entity_id=control.id,
            actor_type="USER",
            actor_id=created_by,
            payload={"control_id": control_id, "framework": framework, "name": name}
        )
        
        logger.info(f"Created security control: {control.id} ({control_id})")
        
        return control
    
    def update_control_status(
        self,
        control_id: str,
        status: str,
        updated_by: str
    ) -> SecurityControl:
        """
        Update control implementation status.
        
        Args:
            control_id: Control ID (ULID string)
            status: New status
            updated_by: User ID updating (ULID string)
            
        Returns:
            Updated SecurityControl instance
            
        Raises:
            ControlNotFoundError: If control not found
        """
        control = self._get_control(control_id)
        old_status = control.status
        
        control.status = status
        control.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(control)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="SECURITY_CONTROL",
            action="STATUS_CHANGED",
            entity_type="security_control",
            entity_id=control_id,
            actor_type="USER",
            actor_id=updated_by,
            payload={"old_status": old_status, "new_status": status}
        )
        
        logger.info(f"Updated control status: {control_id} {old_status} -> {status}")
        
        return control
    
    def get_control(self, control_id: str) -> SecurityControl:
        """
        Get control by ID.
        
        Args:
            control_id: Control ID (ULID string)
            
        Returns:
            SecurityControl instance
            
        Raises:
            ControlNotFoundError: If control not found
        """
        return self._get_control(control_id)
    
    def get_controls_by_framework(self, framework: str) -> List[SecurityControl]:
        """
        Get all controls for a framework.
        
        Args:
            framework: Framework name
            
        Returns:
            List of SecurityControl instances
        """
        return self.db.query(SecurityControl).filter(
            SecurityControl.framework == framework
        ).order_by(SecurityControl.control_id).all()
    
    def list_controls(
        self,
        framework: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[SecurityControl]:
        """
        List controls with filters.
        
        Args:
            framework: Filter by framework
            status: Filter by status
            category: Filter by category
            
        Returns:
            List of SecurityControl instances
        """
        query = self.db.query(SecurityControl)
        
        if framework:
            query = query.filter(SecurityControl.framework == framework)
        if status:
            query = query.filter(SecurityControl.status == status)
        if category:
            query = query.filter(SecurityControl.category == category)
        
        return query.order_by(SecurityControl.framework, SecurityControl.control_id).all()
    
    def get_framework_compliance_summary(self, framework: str) -> Dict[str, Any]:
        """
        Get compliance summary for a framework.
        
        Args:
            framework: Framework name
            
        Returns:
            Dictionary with compliance summary
        """
        controls = self.get_controls_by_framework(framework)
        
        total = len(controls)
        implemented = sum(1 for c in controls if c.status == 'IMPLEMENTED')
        partial = sum(1 for c in controls if c.status == 'PARTIALLY_IMPLEMENTED')
        not_applicable = sum(1 for c in controls if c.status == 'NOT_APPLICABLE')
        
        applicable = total - not_applicable
        compliance_pct = ((implemented + partial * 0.5) / applicable * 100) if applicable > 0 else 100.0
        
        return {
            "framework": framework,
            "total_controls": total,
            "implemented": implemented,
            "partially_implemented": partial,
            "not_implemented": total - implemented - partial - not_applicable,
            "not_applicable": not_applicable,
            "compliance_percentage": round(compliance_pct, 2)
        }
    
    # ==================== Assessments ====================
    
    def create_assessment(
        self,
        control_id: str,
        assessment_date: date,
        effectiveness: str,
        assessor_id: str,
        assessment_type: str = 'INTERNAL',
        maturity_level: Optional[int] = None,
        risk_rating: Optional[str] = None,
        findings: Optional[Dict[str, Any]] = None,
        evidence_bundle_id: Optional[str] = None,
        evidence_summary: Optional[str] = None,
        next_assessment_date: Optional[date] = None
    ) -> ControlAssessment:
        """
        Create a control assessment.
        
        Args:
            control_id: Control ID (ULID string)
            assessment_date: Assessment date
            effectiveness: Effectiveness (EFFECTIVE, PARTIALLY_EFFECTIVE, INEFFECTIVE)
            assessor_id: Assessor user ID (ULID string)
            assessment_type: Assessment type (INTERNAL, EXTERNAL, SELF)
            maturity_level: Maturity level (1-5)
            risk_rating: Risk rating (LOW, MEDIUM, HIGH, CRITICAL)
            findings: Findings dictionary
            evidence_bundle_id: Evidence bundle ID
            evidence_summary: Evidence summary text
            next_assessment_date: Next assessment due date
            
        Returns:
            Created ControlAssessment instance
            
        Raises:
            ControlNotFoundError: If control not found
        """
        control = self._get_control(control_id)
        
        assessment = ControlAssessment(
            id=generate_ulid(),
            control_id=control_id,
            assessment_date=assessment_date,
            assessor_user_id=assessor_id,
            assessment_type=assessment_type,
            effectiveness=effectiveness,
            maturity_level=maturity_level,
            risk_rating=risk_rating,
            findings_json=findings,
            evidence_bundle_id=evidence_bundle_id,
            evidence_summary=evidence_summary,
            next_assessment_date=next_assessment_date,
            created_at=datetime.utcnow()
        )
        
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        
        # Create remediation plan if not effective
        if effectiveness in ['PARTIALLY_EFFECTIVE', 'INEFFECTIVE']:
            self._auto_create_remediation(control, assessment, findings)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="CONTROL_ASSESSMENT",
            action="CREATED",
            entity_type="control_assessment",
            entity_id=assessment.id,
            actor_type="USER",
            actor_id=assessor_id,
            payload={
                "control_id": control.control_id,
                "control_name": control.name,
                "effectiveness": effectiveness,
                "risk_rating": risk_rating,
                "maturity_level": maturity_level
            }
        )
        
        logger.info(f"Created assessment for control {control_id}: {effectiveness}")
        
        return assessment
    
    def get_assessment_history(
        self,
        control_id: str,
        limit: int = 10
    ) -> List[ControlAssessment]:
        """
        Get assessment history for a control.
        
        Args:
            control_id: Control ID (ULID string)
            limit: Maximum number of assessments to return
            
        Returns:
            List of ControlAssessment instances (ordered by date desc)
        """
        return self.db.query(ControlAssessment).filter(
            ControlAssessment.control_id == control_id
        ).order_by(
            ControlAssessment.assessment_date.desc()
        ).limit(limit).all()
    
    def get_overdue_assessments(self) -> List[Dict[str, Any]]:
        """
        Get controls with overdue assessments.
        
        Returns:
            List of dictionaries with overdue assessment details
        """
        today = date.today()
        
        # Get latest assessment for each control
        subquery = self.db.query(
            ControlAssessment.control_id,
            func.max(ControlAssessment.assessment_date).label('latest_date')
        ).group_by(ControlAssessment.control_id).subquery()
        
        # Get assessments with next_assessment_date in the past
        overdue_assessments = self.db.query(ControlAssessment).join(
            subquery,
            and_(
                ControlAssessment.control_id == subquery.c.control_id,
                ControlAssessment.assessment_date == subquery.c.latest_date
            )
        ).filter(
            ControlAssessment.next_assessment_date < today
        ).all()
        
        # Get control details
        result = []
        for assessment in overdue_assessments:
            control = self._get_control(assessment.control_id)
            days_overdue = (today - assessment.next_assessment_date).days
            
            result.append({
                "control_id": control.control_id,
                "control_name": control.name,
                "framework": control.framework,
                "last_assessment": assessment.assessment_date.isoformat(),
                "due_date": assessment.next_assessment_date.isoformat(),
                "days_overdue": days_overdue,
                "effectiveness": assessment.effectiveness
            })
        
        return result
    
    # ==================== Remediation ====================
    
    def create_remediation_plan(
        self,
        control_id: str,
        title: str,
        description: str,
        target_date: date,
        owner_id: str,
        priority: str = 'MEDIUM',
        assessment_id: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> ControlRemediationPlan:
        """
        Create a remediation plan.
        
        Args:
            control_id: Control ID (ULID string)
            title: Plan title
            description: Plan description
            target_date: Target completion date
            owner_id: Owner user ID (ULID string)
            priority: Priority (LOW, MEDIUM, HIGH, CRITICAL)
            assessment_id: Optional assessment ID that triggered this plan
            actions: Optional list of action items
            
        Returns:
            Created ControlRemediationPlan instance
            
        Raises:
            ControlNotFoundError: If control not found
        """
        # Verify control exists
        self._get_control(control_id)
        
        plan = ControlRemediationPlan(
            id=generate_ulid(),
            control_id=control_id,
            assessment_id=assessment_id,
            title=title,
            description=description,
            priority=priority,
            status='PLANNED',
            target_date=target_date,
            owner_user_id=owner_id,
            actions_json=actions or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="REMEDIATION_PLAN",
            action="CREATED",
            entity_type="control_remediation_plan",
            entity_id=plan.id,
            actor_type="USER",
            actor_id=owner_id,
            payload={
                "control_id": control_id,
                "title": title,
                "priority": priority,
                "target_date": target_date.isoformat()
            }
        )
        
        logger.info(f"Created remediation plan: {plan.id} for control {control_id}")
        
        return plan
    
    def update_remediation_status(
        self,
        plan_id: str,
        status: str,
        updated_by: str,
        completion_date: Optional[date] = None
    ) -> ControlRemediationPlan:
        """
        Update remediation plan status.
        
        Args:
            plan_id: Plan ID (ULID string)
            status: New status
            updated_by: User ID updating (ULID string)
            completion_date: Optional completion date
            
        Returns:
            Updated ControlRemediationPlan instance
            
        Raises:
            RemediationPlanNotFoundError: If plan not found
        """
        plan = self._get_remediation_plan(plan_id)
        old_status = plan.status
        
        plan.status = status
        if status == 'COMPLETED':
            plan.completion_date = completion_date or date.today()
        plan.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(plan)
        
        # Audit
        self.audit.append_event(
            tenant_id=None,
            event_type="REMEDIATION_PLAN",
            action="STATUS_CHANGED",
            entity_type="control_remediation_plan",
            entity_id=plan_id,
            actor_type="USER",
            actor_id=updated_by,
            payload={"old_status": old_status, "new_status": status}
        )
        
        logger.info(f"Updated remediation plan status: {plan_id} {old_status} -> {status}")
        
        return plan
    
    def get_open_remediations(
        self,
        priority: Optional[str] = None
    ) -> List[ControlRemediationPlan]:
        """
        Get open remediation plans.
        
        Args:
            priority: Optional priority filter
            
        Returns:
            List of ControlRemediationPlan instances
        """
        query = self.db.query(ControlRemediationPlan).filter(
            ControlRemediationPlan.status.in_(['PLANNED', 'IN_PROGRESS'])
        )
        
        if priority:
            query = query.filter(ControlRemediationPlan.priority == priority)
        
        return query.order_by(ControlRemediationPlan.target_date).all()
    
    # ==================== Reports ====================
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report.
        
        Returns:
            Dictionary with compliance report data
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "frameworks": {},
            "overall_stats": {
                "total_controls": 0,
                "assessed_controls": 0,
                "open_remediations": 0,
                "overdue_assessments": 0
            }
        }
        
        for framework in self.FRAMEWORKS:
            controls = self.get_controls_by_framework(framework)
            if controls:
                report["frameworks"][framework] = self.get_framework_compliance_summary(framework)
                report["overall_stats"]["total_controls"] += len(controls)
        
        # Count assessed controls (controls with at least one assessment)
        assessed_count = self.db.query(
            func.count(func.distinct(ControlAssessment.control_id))
        ).scalar() or 0
        report["overall_stats"]["assessed_controls"] = assessed_count
        
        report["overall_stats"]["open_remediations"] = len(self.get_open_remediations())
        report["overall_stats"]["overdue_assessments"] = len(self.get_overdue_assessments())
        
        return report
    
    # ==================== Private Methods ====================
    
    def _get_control(self, control_id: str) -> SecurityControl:
        """
        Get control by ID.
        
        Args:
            control_id: Control ID (ULID string)
            
        Returns:
            SecurityControl instance
            
        Raises:
            ControlNotFoundError: If control not found
        """
        control = self.db.query(SecurityControl).filter(
            SecurityControl.id == control_id
        ).first()
        if not control:
            raise ControlNotFoundError(f"Control {control_id} not found")
        return control
    
    def _get_remediation_plan(self, plan_id: str) -> ControlRemediationPlan:
        """
        Get remediation plan by ID.
        
        Args:
            plan_id: Plan ID (ULID string)
            
        Returns:
            ControlRemediationPlan instance
            
        Raises:
            RemediationPlanNotFoundError: If plan not found
        """
        plan = self.db.query(ControlRemediationPlan).filter(
            ControlRemediationPlan.id == plan_id
        ).first()
        if not plan:
            raise RemediationPlanNotFoundError(f"Remediation plan {plan_id} not found")
        return plan
    
    def _auto_create_remediation(
        self,
        control: SecurityControl,
        assessment: ControlAssessment,
        findings: Optional[Dict[str, Any]]
    ):
        """
        Auto-create remediation plan for ineffective controls.
        
        Args:
            control: SecurityControl instance
            assessment: ControlAssessment instance
            findings: Optional findings dictionary
        """
        gaps = findings.get('gaps', []) if findings else []
        recommendations = findings.get('recommendations', []) if findings else []
        
        actions = [
            {"action": rec, "status": "PENDING", "owner": None}
            for rec in recommendations[:5]  # Max 5 actions
        ]
        
        priority = 'HIGH' if assessment.effectiveness == 'INEFFECTIVE' else 'MEDIUM'
        
        try:
            self.create_remediation_plan(
                control_id=control.id,
                title=f"Remediation for {control.control_id}",
                description=f"Address gaps identified in assessment: {', '.join(gaps[:3]) if gaps else 'Control not effective'}",
                target_date=date.today() + timedelta(days=90),  # 90 day default
                owner_id=control.owner_user_id or assessment.assessor_user_id,
                priority=priority,
                assessment_id=assessment.id,
                actions=actions
            )
            logger.info(f"Auto-created remediation plan for control {control.control_id}")
        except Exception as e:
            logger.error(f"Failed to auto-create remediation plan: {e}", exc_info=True)
            # Don't fail the assessment creation if remediation creation fails


# Exception classes
class ControlNotFoundError(Exception):
    """Security control not found"""
    pass


class ControlExistsError(Exception):
    """Security control already exists"""
    pass


class InvalidFrameworkError(Exception):
    """Invalid framework"""
    pass


class RemediationPlanNotFoundError(Exception):
    """Remediation plan not found"""
    pass
