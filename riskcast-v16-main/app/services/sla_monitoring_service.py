"""
SLA monitoring service.

Tracks SLA compliance and breaches.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.sla import SLADefinition, SLAMeasurement, SLABreach
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class SLAMonitoringService:
    """Service for SLA monitoring."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize SLA monitoring service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    # ==================== SLA Definitions ====================
    
    def create_sla(
        self,
        name: str,
        category: str,
        metric_name: str,
        target_value: float,
        comparison: str,
        created_by: str,
        tenant_id: Optional[str] = None,
        description: Optional[str] = None,
        metric_unit: Optional[str] = None,
        warning_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        measurement_window: Optional[str] = None,
        measurement_config: Optional[Dict[str, Any]] = None,
        contract_reference: Optional[str] = None,
        penalty_config: Optional[Dict[str, Any]] = None
    ) -> SLADefinition:
        """
        Create a new SLA definition.
        
        Args:
            name: SLA name
            category: Category (AVAILABILITY, RESPONSE_TIME, PROCESSING_TIME, DATA_QUALITY)
            metric_name: Metric name
            target_value: Target value
            comparison: Comparison operator (>=, <=, ==)
            created_by: User ID creating (ULID string)
            tenant_id: Optional tenant ID (ULID string)
            ... other optional fields
            
        Returns:
            Created SLADefinition instance
        """
        sla = SLADefinition(
            id=generate_ulid(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            category=category,
            metric_name=metric_name,
            metric_unit=metric_unit,
            target_value=target_value,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            comparison=comparison,
            measurement_window=measurement_window,
            measurement_config_json=measurement_config,
            contract_reference=contract_reference,
            penalty_config_json=penalty_config,
            status='ACTIVE',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(sla)
        self.db.commit()
        self.db.refresh(sla)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="SLA",
            action="CREATED",
            entity_type="sla_definition",
            entity_id=sla.id,
            actor_type="USER",
            actor_id=created_by,
            payload={"name": name, "category": category, "target_value": target_value}
        )
        
        logger.info(f"Created SLA definition: {sla.id} ({name})")
        
        return sla
    
    def get_active_slas(
        self,
        tenant_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[SLADefinition]:
        """
        Get active SLA definitions.
        
        Args:
            tenant_id: Optional tenant ID to filter
            category: Optional category to filter
            
        Returns:
            List of active SLADefinition instances
        """
        query = self.db.query(SLADefinition).filter(
            SLADefinition.status == 'ACTIVE'
        )
        
        if tenant_id:
            query = query.filter(
                or_(
                    SLADefinition.tenant_id == tenant_id,
                    SLADefinition.tenant_id.is_(None)
                )
            )
        
        if category:
            query = query.filter(SLADefinition.category == category)
        
        return query.all()
    
    def get_sla(self, sla_id: str) -> SLADefinition:
        """
        Get SLA definition by ID.
        
        Args:
            sla_id: SLA definition ID (ULID string)
            
        Returns:
            SLADefinition instance
            
        Raises:
            SLANotFoundError: If SLA not found
        """
        sla = self.db.query(SLADefinition).filter(
            SLADefinition.id == sla_id
        ).first()
        if not sla:
            raise SLANotFoundError(f"SLA {sla_id} not found")
        return sla
    
    # ==================== Measurements ====================
    
    def record_measurement(
        self,
        sla_definition_id: str,
        period_start: datetime,
        period_end: datetime,
        measured_value: float,
        tenant_id: Optional[str] = None,
        sample_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> SLAMeasurement:
        """
        Record an SLA measurement.
        
        Args:
            sla_definition_id: SLA definition ID (ULID string)
            period_start: Period start timestamp
            period_end: Period end timestamp
            measured_value: Measured value
            tenant_id: Optional tenant ID (ULID string)
            sample_count: Optional sample count
            details: Optional details dictionary
            
        Returns:
            Created SLAMeasurement instance
        """
        sla = self.get_sla(sla_definition_id)
        
        # Determine status
        status = self._evaluate_measurement(sla, measured_value)
        
        measurement = SLAMeasurement(
            id=generate_ulid(),
            sla_definition_id=sla_definition_id,
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            measured_value=measured_value,
            target_value=sla.target_value,
            status=status,
            sample_count=sample_count,
            details_json=details,
            measured_at=datetime.utcnow()
        )
        
        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        
        # Create breach if applicable
        if status in ['WARNING', 'BREACHED']:
            self._create_breach(sla, measurement)
        
        logger.info(f"Recorded measurement for SLA {sla_definition_id}: {measured_value} (status: {status})")
        
        return measurement
    
    def _evaluate_measurement(
        self,
        sla: SLADefinition,
        measured_value: float
    ) -> str:
        """
        Evaluate if measurement meets SLA.
        
        Args:
            sla: SLADefinition instance
            measured_value: Measured value
            
        Returns:
            Status: 'MET', 'WARNING', or 'BREACHED'
        """
        comparison = sla.comparison
        target = sla.target_value
        warning = sla.warning_threshold
        critical = sla.critical_threshold
        
        # Check against comparison
        if comparison == '>=':
            meets_target = measured_value >= target
            meets_warning = measured_value >= warning if warning is not None else True
            meets_critical = measured_value >= critical if critical is not None else True
        elif comparison == '<=':
            meets_target = measured_value <= target
            meets_warning = measured_value <= warning if warning is not None else True
            meets_critical = measured_value <= critical if critical is not None else True
        elif comparison == '==':
            tolerance = target * 0.01  # 1% tolerance
            meets_target = abs(measured_value - target) <= tolerance
            meets_warning = True
            meets_critical = True
        else:
            meets_target = True
            meets_warning = True
            meets_critical = True
        
        if meets_target:
            return 'MET'
        elif not meets_critical and critical is not None:
            return 'BREACHED'
        elif not meets_warning and warning is not None:
            return 'WARNING'
        else:
            return 'MET'
    
    def _create_breach(
        self,
        sla: SLADefinition,
        measurement: SLAMeasurement
    ) -> SLABreach:
        """
        Create a breach record.
        
        Args:
            sla: SLADefinition instance
            measurement: SLAMeasurement instance
            
        Returns:
            Created SLABreach instance
        """
        severity = 'CRITICAL' if measurement.status == 'BREACHED' else 'WARNING'
        variance = measurement.measured_value - sla.target_value
        
        breach = SLABreach(
            id=generate_ulid(),
            sla_definition_id=sla.id,
            measurement_id=measurement.id,
            tenant_id=measurement.tenant_id,
            severity=severity,
            target_value=sla.target_value,
            actual_value=measurement.measured_value,
            variance=variance,
            status='OPEN',
            occurred_at=measurement.period_end,
            created_at=datetime.utcnow()
        )
        
        self.db.add(breach)
        self.db.commit()
        self.db.refresh(breach)
        
        # Audit
        self.audit.append_event(
            tenant_id=measurement.tenant_id,
            event_type="SLA",
            action="BREACH_DETECTED",
            entity_type="sla_breach",
            entity_id=breach.id,
            actor_type="SYSTEM",
            actor_id="SLA_MONITORING_SERVICE",
            payload={
                "sla_name": sla.name,
                "sla_id": sla.id,
                "severity": severity,
                "target": sla.target_value,
                "actual": measurement.measured_value,
                "variance": variance
            }
        )
        
        logger.warning(f"SLA breach detected: {breach.id} for SLA {sla.id} ({sla.name})")
        
        return breach
    
    # ==================== Breach Management ====================
    
    def acknowledge_breach(
        self,
        breach_id: str,
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> SLABreach:
        """
        Acknowledge a breach.
        
        Args:
            breach_id: Breach ID (ULID string)
            acknowledged_by: User ID acknowledging (ULID string)
            notes: Optional notes
            
        Returns:
            Updated SLABreach instance
            
        Raises:
            BreachNotFoundError: If breach not found
            InvalidBreachStateError: If breach is not in OPEN status
        """
        breach = self._get_breach(breach_id)
        
        if breach.status != 'OPEN':
            raise InvalidBreachStateError(f"Breach is {breach.status}, cannot acknowledge")
        
        breach.status = 'ACKNOWLEDGED'
        breach.acknowledged_at = datetime.utcnow()
        breach.acknowledged_by_user_id = acknowledged_by
        if notes:
            breach.resolution_notes = notes
        
        self.db.commit()
        self.db.refresh(breach)
        
        # Audit
        self.audit.append_event(
            tenant_id=breach.tenant_id,
            event_type="SLA",
            action="BREACH_ACKNOWLEDGED",
            entity_type="sla_breach",
            entity_id=breach_id,
            actor_type="USER",
            actor_id=acknowledged_by,
            payload={"notes": notes}
        )
        
        logger.info(f"Breach acknowledged: {breach_id} by {acknowledged_by}")
        
        return breach
    
    def resolve_breach(
        self,
        breach_id: str,
        resolved_by: str,
        root_cause: str,
        resolution_notes: str
    ) -> SLABreach:
        """
        Resolve a breach.
        
        Args:
            breach_id: Breach ID (ULID string)
            resolved_by: User ID resolving (ULID string)
            root_cause: Root cause description
            resolution_notes: Resolution notes
            
        Returns:
            Updated SLABreach instance
            
        Raises:
            BreachNotFoundError: If breach not found
            InvalidBreachStateError: If breach is not in OPEN or ACKNOWLEDGED status
        """
        breach = self._get_breach(breach_id)
        
        if breach.status not in ['OPEN', 'ACKNOWLEDGED']:
            raise InvalidBreachStateError(f"Breach is {breach.status}, cannot resolve")
        
        breach.status = 'RESOLVED'
        breach.root_cause = root_cause
        breach.resolution_notes = resolution_notes
        breach.resolved_at = datetime.utcnow()
        breach.resolved_by_user_id = resolved_by
        
        self.db.commit()
        self.db.refresh(breach)
        
        # Audit
        self.audit.append_event(
            tenant_id=breach.tenant_id,
            event_type="SLA",
            action="BREACH_RESOLVED",
            entity_type="sla_breach",
            entity_id=breach_id,
            actor_type="USER",
            actor_id=resolved_by,
            payload={"root_cause": root_cause}
        )
        
        logger.info(f"Breach resolved: {breach_id} by {resolved_by}")
        
        return breach
    
    def apply_penalty(
        self,
        breach_id: str,
        amount_cents: int,
        currency: str,
        applied_by: str
    ) -> SLABreach:
        """
        Apply penalty for a breach.
        
        Args:
            breach_id: Breach ID (ULID string)
            amount_cents: Penalty amount in cents
            currency: Currency code (e.g., 'USD')
            applied_by: User ID applying penalty (ULID string)
            
        Returns:
            Updated SLABreach instance
            
        Raises:
            BreachNotFoundError: If breach not found
        """
        breach = self._get_breach(breach_id)
        
        breach.penalty_applied = True
        breach.penalty_amount_cents = amount_cents
        breach.penalty_currency = currency
        breach.status = 'CREDITED'
        
        self.db.commit()
        self.db.refresh(breach)
        
        # Audit
        self.audit.append_event(
            tenant_id=breach.tenant_id,
            event_type="SLA",
            action="PENALTY_APPLIED",
            entity_type="sla_breach",
            entity_id=breach_id,
            actor_type="USER",
            actor_id=applied_by,
            payload={
                "amount_cents": amount_cents,
                "currency": currency
            }
        )
        
        logger.info(f"Penalty applied to breach {breach_id}: {amount_cents} {currency}")
        
        return breach
    
    # ==================== Reporting ====================
    
    def get_sla_compliance_report(
        self,
        tenant_id: Optional[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate SLA compliance report.
        
        Args:
            tenant_id: Optional tenant ID (ULID string)
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dictionary with compliance report data
        """
        slas = self.get_active_slas(tenant_id)
        
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "overall_compliance": 0.0,
            "sla_details": [],
            "breaches": {
                "total": 0,
                "open": 0,
                "acknowledged": 0,
                "resolved": 0,
                "credited": 0
            }
        }
        
        total_measurements = 0
        met_measurements = 0
        
        for sla in slas:
            measurements = self.db.query(SLAMeasurement).filter(
                SLAMeasurement.sla_definition_id == sla.id,
                SLAMeasurement.period_start >= start_date,
                SLAMeasurement.period_end <= end_date
            ).all()
            
            breaches = self.db.query(SLABreach).filter(
                SLABreach.sla_definition_id == sla.id,
                SLABreach.occurred_at >= start_date,
                SLABreach.occurred_at <= end_date
            ).all()
            
            met = sum(1 for m in measurements if m.status == 'MET')
            total = len(measurements)
            
            total_measurements += total
            met_measurements += met
            
            compliance_pct = (met / total * 100) if total > 0 else 100.0
            
            report["sla_details"].append({
                "sla_id": sla.id,
                "name": sla.name,
                "category": sla.category,
                "target": sla.target_value,
                "measurements": total,
                "met": met,
                "breached": total - met,
                "compliance_pct": round(compliance_pct, 2)
            })
            
            report["breaches"]["total"] += len(breaches)
            report["breaches"]["open"] += sum(1 for b in breaches if b.status == 'OPEN')
            report["breaches"]["acknowledged"] += sum(1 for b in breaches if b.status == 'ACKNOWLEDGED')
            report["breaches"]["resolved"] += sum(1 for b in breaches if b.status == 'RESOLVED')
            report["breaches"]["credited"] += sum(1 for b in breaches if b.status == 'CREDITED')
        
        report["overall_compliance"] = round(
            (met_measurements / total_measurements * 100) if total_measurements > 0 else 100.0,
            2
        )
        
        return report
    
    def list_breaches(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        sla_definition_id: Optional[str] = None,
        limit: int = 100
    ) -> List[SLABreach]:
        """
        List breaches with filters.
        
        Args:
            tenant_id: Optional tenant ID to filter
            status: Optional status to filter
            severity: Optional severity to filter
            sla_definition_id: Optional SLA definition ID to filter
            limit: Maximum number of results
            
        Returns:
            List of SLABreach instances
        """
        query = self.db.query(SLABreach)
        
        if tenant_id:
            query = query.filter(SLABreach.tenant_id == tenant_id)
        if status:
            query = query.filter(SLABreach.status == status)
        if severity:
            query = query.filter(SLABreach.severity == severity)
        if sla_definition_id:
            query = query.filter(SLABreach.sla_definition_id == sla_definition_id)
        
        return query.order_by(SLABreach.occurred_at.desc()).limit(limit).all()
    
    def _get_breach(self, breach_id: str) -> SLABreach:
        """
        Get breach by ID.
        
        Args:
            breach_id: Breach ID (ULID string)
            
        Returns:
            SLABreach instance
            
        Raises:
            BreachNotFoundError: If breach not found
        """
        breach = self.db.query(SLABreach).filter(
            SLABreach.id == breach_id
        ).first()
        if not breach:
            raise BreachNotFoundError(f"Breach {breach_id} not found")
        return breach


# Exception classes
class SLANotFoundError(Exception):
    """SLA definition not found"""
    pass


class BreachNotFoundError(Exception):
    """SLA breach not found"""
    pass


class InvalidBreachStateError(Exception):
    """Invalid breach state for operation"""
    pass
