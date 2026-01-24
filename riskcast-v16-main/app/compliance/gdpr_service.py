"""
GDPR Compliance Service

Implements GDPR requirements:
1. Right to Access (Article 15) - Export all user data
2. Right to Rectification (Article 16) - Correct inaccurate data
3. Right to Erasure (Article 17) - Delete user data
4. Right to Portability (Article 20) - Export in machine-readable format
5. Data Processing Records (Article 30)

CRITICAL: Audit trail MUST be preserved even after data deletion
(regulatory requirement for insurance).
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Session

from app.core.audit.immutable_ledger import ImmutableAuditLedger
from app.core.evidence.storage import EvidenceStorage
from app.database import Base
from app.modules.tenancy.models import User

logger = logging.getLogger(__name__)


class GDPRRequestType(str, Enum):
    """Types of GDPR requests."""

    ACCESS = "ACCESS"
    RECTIFICATION = "RECTIFICATION"
    ERASURE = "ERASURE"
    PORTABILITY = "PORTABILITY"
    OBJECTION = "OBJECTION"
    RESTRICTION = "RESTRICTION"


class GDPRRequestStatus(str, Enum):
    """Status of GDPR request."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"


@dataclass
class DataExportResult:
    """Result of data export request."""

    request_id: str
    user_id: str
    export_format: str
    file_location: str
    file_hash: str
    file_size_bytes: int
    categories_exported: List[str]
    record_counts: Dict[str, int]
    exported_at: datetime
    expires_at: datetime


@dataclass
class ErasureResult:
    """Result of data erasure request."""

    request_id: str
    user_id: str
    categories_erased: List[str]
    categories_retained: List[str]
    retention_reasons: Dict[str, str]
    records_deleted: int
    records_anonymized: int
    completed_at: datetime


class GDPRRequestModel(Base):
    """GDPR request tracking model."""

    __tablename__ = "gdpr_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(26), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    response_deadline = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    result_location = Column(String(500), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    tenant_id = Column(String(26), nullable=True, index=True)

    __table_args__ = (
        Index("idx_gdpr_requests_user", "user_id"),
        Index("idx_gdpr_requests_status", "status"),
        Index("idx_gdpr_requests_type", "request_type"),
    )


class GDPRService:
    """
    Service for handling GDPR compliance requests.

    Key principles:
    1. User data can be exported or deleted
    2. Audit trail is PRESERVED (anonymized, not deleted)
    3. Insurance records may be retained for regulatory periods
    4. All GDPR requests are themselves audited
    """

    RETENTION_PERIODS = {
        "policy": 10,
        "claim": 10,
        "audit": 7,
        "risk_assessment": 7,
        "quote": 3,
        "user_preferences": 0,
        "communication": 3,
    }

    DELETABLE_CATEGORIES = [
        "user_preferences",
        "communication",
        "draft_quotes",
        "temporary_data",
    ]

    ANONYMIZABLE_CATEGORIES = [
        "policy",
        "claim",
        "risk_assessment",
        "audit_events",
    ]

    def __init__(
        self,
        db: Session,
        audit: ImmutableAuditLedger,
        storage: EvidenceStorage,
    ):
        self.db = db
        self.audit = audit
        self.storage = storage
        self.logger = logging.getLogger(__name__)

    def handle_access_request(
        self,
        user_id: str,
        requested_categories: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> DataExportResult:
        """
        Handle GDPR Article 15 - Right of Access.

        Exports all user data in a structured format.
        """
        request_id = str(uuid.uuid4())
        deadline = datetime.utcnow() + timedelta(days=30)

        request = GDPRRequestModel(
            id=request_id,
            request_type=GDPRRequestType.ACCESS.value,
            user_id=user_id,
            user_email="",  # Set below
            status=GDPRRequestStatus.PROCESSING.value,
            response_deadline=deadline,
            tenant_id=tenant_id,
        )
        self.db.add(request)
        self.db.flush()

        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            request.user_email = user.email

        self.audit.append_event(
            event_type="GDPR",
            action="ACCESS_REQUEST_RECEIVED",
            entity_type="gdpr_request",
            entity_id=request_id,
            actor_type="USER",
            actor_id=user_id,
            tenant_id=tenant_id,
            payload={
                "request_type": "ACCESS",
                "categories_requested": requested_categories,
            },
        )

        export_data = self._collect_user_data(user_id, requested_categories, tenant_id)
        export_bytes, file_hash = self._create_export_file(export_data, format="JSON")
        storage_path = f"gdpr/exports/{request_id}/{user_id}/data_export.json"
        file_location = self.storage.upload(export_bytes, storage_path)

        result = DataExportResult(
            request_id=request_id,
            user_id=user_id,
            export_format="JSON",
            file_location=file_location,
            file_hash=file_hash,
            file_size_bytes=len(export_bytes),
            categories_exported=list(export_data.keys()),
            record_counts={
                k: len(v) if isinstance(v, list) else 1
                for k, v in export_data.items()
            },
            exported_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )

        request.status = GDPRRequestStatus.COMPLETED.value
        request.completed_at = datetime.utcnow()
        request.result_location = file_location
        request.metadata_json = {
            "categories_exported": result.categories_exported,
            "record_counts": result.record_counts,
            "file_hash": file_hash,
        }
        self.db.commit()

        self.audit.append_event(
            event_type="GDPR",
            action="ACCESS_REQUEST_COMPLETED",
            entity_type="gdpr_request",
            entity_id=request_id,
            actor_type="SYSTEM",
            tenant_id=tenant_id,
            payload={
                "categories_exported": result.categories_exported,
                "record_counts": result.record_counts,
                "file_hash": result.file_hash,
            },
        )

        return result

    def handle_erasure_request(
        self,
        user_id: str,
        reason: str,
        tenant_id: Optional[str] = None,
    ) -> ErasureResult:
        """
        Handle GDPR Article 17 - Right to Erasure.

        IMPORTANT: Some data must be retained for regulatory compliance.
        This data is ANONYMIZED, not deleted.
        """
        request_id = str(uuid.uuid4())
        deadline = datetime.utcnow() + timedelta(days=30)

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        request = GDPRRequestModel(
            id=request_id,
            request_type=GDPRRequestType.ERASURE.value,
            user_id=user_id,
            user_email=user.email,
            status=GDPRRequestStatus.PROCESSING.value,
            response_deadline=deadline,
            notes=reason,
            tenant_id=tenant_id,
        )
        self.db.add(request)
        self.db.flush()

        self.audit.append_event(
            event_type="GDPR",
            action="ERASURE_REQUEST_RECEIVED",
            entity_type="gdpr_request",
            entity_id=request_id,
            actor_type="USER",
            actor_id=user_id,
            tenant_id=tenant_id,
            payload={"request_type": "ERASURE", "reason": reason},
        )

        categories_erased = []
        categories_retained = []
        retention_reasons = {}
        records_deleted = 0
        records_anonymized = 0

        for category in self.DELETABLE_CATEGORIES:
            count = self._delete_category_data(user_id, category, tenant_id)
            if count > 0:
                categories_erased.append(category)
                records_deleted += count

        for category in self.ANONYMIZABLE_CATEGORIES:
            retention_period = self.RETENTION_PERIODS.get(category, 0)
            if retention_period > 0:
                oldest_allowed = datetime.utcnow() - timedelta(
                    days=retention_period * 365
                )
                count = self._anonymize_category_data(
                    user_id, category, older_than=oldest_allowed, tenant_id=tenant_id
                )
                if count > 0:
                    categories_retained.append(category)
                    retention_reasons[category] = (
                        f"Retained for {retention_period} years per insurance regulations"
                    )
                    records_anonymized += count

        audit_count = self._anonymize_audit_trail(user_id, tenant_id)
        if audit_count > 0:
            categories_retained.append("audit_trail")
            retention_reasons["audit_trail"] = (
                "Audit trail anonymized but retained for regulatory compliance"
            )
            records_anonymized += audit_count

        self._anonymize_user_account(user_id)

        result = ErasureResult(
            request_id=request_id,
            user_id=user_id,
            categories_erased=categories_erased,
            categories_retained=categories_retained,
            retention_reasons=retention_reasons,
            records_deleted=records_deleted,
            records_anonymized=records_anonymized,
            completed_at=datetime.utcnow(),
        )

        request.status = GDPRRequestStatus.COMPLETED.value
        request.completed_at = datetime.utcnow()
        request.metadata_json = {
            "categories_erased": categories_erased,
            "categories_retained": categories_retained,
            "records_deleted": records_deleted,
            "records_anonymized": records_anonymized,
        }
        self.db.commit()

        self.audit.append_event(
            event_type="GDPR",
            action="ERASURE_REQUEST_COMPLETED",
            entity_type="gdpr_request",
            entity_id=request_id,
            actor_type="SYSTEM",
            tenant_id=tenant_id,
            payload={
                "categories_erased": categories_erased,
                "categories_retained": categories_retained,
                "records_deleted": records_deleted,
                "records_anonymized": records_anonymized,
            },
        )

        return result

    def handle_portability_request(
        self, user_id: str, tenant_id: Optional[str] = None
    ) -> DataExportResult:
        """
        Handle GDPR Article 20 - Right to Data Portability.

        Exports data in machine-readable format (JSON).
        """
        return self.handle_access_request(
            user_id,
            requested_categories=[
                "profile",
                "policies",
                "quotes",
                "claims",
                "risk_assessments",
            ],
            tenant_id=tenant_id,
        )

    def get_processing_records(
        self, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate GDPR Article 30 - Records of Processing Activities.

        Required documentation for data controllers.
        """
        return {
            "controller": {
                "name": "RISKCAST Insurance Platform",
                "contact": "dpo@riskcast.com",
            },
            "processing_purposes": [
                {
                    "purpose": "Insurance underwriting",
                    "legal_basis": "Contract performance",
                    "data_categories": ["shipment_data", "cargo_data", "route_data"],
                    "retention_period": "10 years",
                },
                {
                    "purpose": "Claims processing",
                    "legal_basis": "Contract performance",
                    "data_categories": ["claim_data", "evidence", "loss_data"],
                    "retention_period": "10 years",
                },
                {
                    "purpose": "Risk assessment",
                    "legal_basis": "Legitimate interest",
                    "data_categories": ["risk_factors", "historical_data"],
                    "retention_period": "7 years",
                },
                {
                    "purpose": "Regulatory compliance",
                    "legal_basis": "Legal obligation",
                    "data_categories": ["audit_logs", "decision_records"],
                    "retention_period": "7 years",
                },
            ],
            "data_recipients": [
                "Reinsurers (for policy binding)",
                "Regulatory authorities (on request)",
                "Auditors (for compliance verification)",
            ],
            "international_transfers": [
                {
                    "destination": "Cloud providers (AWS)",
                    "safeguards": "Standard Contractual Clauses",
                }
            ],
            "security_measures": [
                "Encryption at rest and in transit",
                "Access control and authentication",
                "Audit logging",
                "Regular security assessments",
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _collect_user_data(
        self,
        user_id: str,
        categories: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Collect all user data for export."""
        data = {}

        if not categories or "profile" in categories:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                data["profile"] = {
                    "id": str(user.id),
                    "email": user.email,
                    "status": user.status.value if hasattr(user.status, "value") else str(user.status),
                    "created_at": user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None,
                }
                from app.models.account import UserPreference
                pref = self.db.query(UserPreference).filter(
                    UserPreference.user_id == int(user_id) if user_id.isdigit() else None
                ).first()
                if pref:
                    data["preferences"] = {
                        "timezone": pref.timezone,
                        "currency": pref.currency,
                        "units": pref.units,
                        "theme": pref.theme,
                        "preferences_json": pref.preferences_json,
                    }

        if not categories or "policies" in categories:
            from app.modules.underwriting.models import Policy

            query = self.db.query(Policy)
            if tenant_id:
                query = query.filter(Policy.tenant_id == tenant_id)
            query = query.filter(Policy.bound_by_user_id == user_id)
            policies = query.all()
            data["policies"] = [
                {
                    "id": str(p.id),
                    "policy_number": p.policy_number,
                    "status": p.status.value if hasattr(p.status, "value") else str(p.status),
                    "effective_from": p.effective_from.isoformat() if p.effective_from else None,
                    "effective_to": p.effective_to.isoformat() if p.effective_to else None,
                    "terms": p.terms_json,
                }
                for p in policies
            ]

        if not categories or "claims" in categories:
            from app.modules.claims.models import Claim

            query = self.db.query(Claim)
            if tenant_id:
                query = query.filter(Claim.tenant_id == tenant_id)
            query = query.filter(Claim.created_by_user_id == user_id)
            claims = query.all()
            data["claims"] = [
                {
                    "id": str(c.id),
                    "claim_number": c.claim_number,
                    "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                    "filed_at": c.created_at.isoformat() if hasattr(c, "created_at") and c.created_at else None,
                    "fnol": c.fnol_json,
                }
                for c in claims
            ]

        if not categories or "risk_assessments" in categories:
            from app.models.risk_assessment import RiskAssessment

            query = self.db.query(RiskAssessment)
            if tenant_id:
                query = query.filter(RiskAssessment.tenant_id == tenant_id)
            query = query.filter(
                RiskAssessment.created_by_user_id == user_id
            )
            assessments = query.all()
            data["risk_assessments"] = [
                {
                    "id": str(a.id),
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "input_hash": a.input_hash,
                }
                for a in assessments
            ]

            from app.models.risk_run import RiskRun

            query = self.db.query(RiskRun)
            if tenant_id:
                query = query.filter(RiskRun.tenant_id == tenant_id)
            query = query.filter(RiskRun.assessment_id.in_([a.id for a in assessments]))
            risk_runs = query.all()
            data["risk_runs"] = [
                {
                    "id": str(r.id),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "overall_risk_score": (r.result_json or {}).get("overall_risk_score"),
                    "input_summary": {},
                }
                for r in risk_runs
            ]

        if not categories or "activity_log" in categories:
            events = self.audit.get_events_by_actor(
                actor_type="USER",
                actor_id=user_id,
            )
            data["activity_log"] = [
                {
                    "timestamp": e.event_timestamp.isoformat(),
                    "action": e.action,
                    "entity_type": e.entity_type,
                }
                for e in events[:1000]
            ]

        return data

    def _create_export_file(
        self, data: Dict[str, Any], format: str = "JSON"
    ) -> Tuple[bytes, str]:
        """Create export file and compute hash."""
        if format == "JSON":
            content = json.dumps(data, indent=2, default=str)
            content_bytes = content.encode("utf-8")
        else:
            raise ValueError(f"Unsupported format: {format}")

        file_hash = hashlib.sha256(content_bytes).hexdigest()
        return content_bytes, file_hash

    def _delete_category_data(
        self, user_id: str, category: str, tenant_id: Optional[str] = None
    ) -> int:
        """Delete data for a category. Returns count deleted."""
        count = 0
        if category == "user_preferences":
            try:
                from app.models.account import UserPreference
                user_id_int = int(user_id)
                query = self.db.query(UserPreference).filter(
                    UserPreference.user_id == user_id_int
                )
                count = query.count()
                query.delete(synchronize_session=False)
            except (ValueError, TypeError):
                pass

        if category == "communication":
            pass

        if category == "draft_quotes":
            from app.models.quote import Quote
            query = self.db.query(Quote)
            if tenant_id:
                query = query.filter(Quote.tenant_id == tenant_id)
            query = query.filter(
                Quote.issued_by_user_id == user_id,
                Quote.status == "DRAFT"
            )
            count = query.count()
            query.delete(synchronize_session=False)

        self.db.commit()
        return count

    def _anonymize_category_data(
        self,
        user_id: str,
        category: str,
        older_than: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Anonymize data for a category. Returns count anonymized."""
        count = 0

        if category == "policy":
            from app.modules.underwriting.models import Policy

            query = self.db.query(Policy)
            if tenant_id:
                query = query.filter(Policy.tenant_id == tenant_id)
            query = query.filter(Policy.bound_by_user_id == user_id)
            if older_than:
                query = query.filter(Policy.created_at < older_than)

            for policy in query.all():
                policy.bound_by_user_id = None
                if hasattr(policy, "policyholder_json") and policy.policyholder_json:
                    policyholder = policy.policyholder_json or {}
                    if "email" in policyholder:
                        policyholder["email"] = f"anonymized_{policy.id[:12]}@deleted.local"
                    if "name" in policyholder:
                        policyholder["name"] = f"Anonymized Policyholder"
                    policy.policyholder_json = policyholder
                count += 1

        elif category == "claim":
            from app.modules.claims.models import Claim

            query = self.db.query(Claim)
            if tenant_id:
                query = query.filter(Claim.tenant_id == tenant_id)
            query = query.filter(Claim.created_by_user_id == user_id)
            if older_than and hasattr(Claim, "created_at"):
                query = query.filter(Claim.created_at < older_than)

            for claim in query.all():
                claim.created_by_user_id = None
                if hasattr(claim, "assigned_adjuster_id"):
                    claim.assigned_adjuster_id = None
                if hasattr(claim, "decision_by_user_id"):
                    claim.decision_by_user_id = None
                count += 1

        elif category == "risk_assessment":
            from app.models.risk_assessment import RiskAssessment

            query = self.db.query(RiskAssessment)
            if tenant_id:
                query = query.filter(RiskAssessment.tenant_id == tenant_id)
            query = query.filter(RiskAssessment.created_by_user_id == user_id)
            if older_than:
                query = query.filter(RiskAssessment.created_at < older_than)

            for assessment in query.all():
                assessment.created_by_user_id = None
                count += 1

        elif category == "quote":
            from app.models.quote import Quote

            query = self.db.query(Quote)
            if tenant_id:
                query = query.filter(Quote.tenant_id == tenant_id)
            query = query.filter(Quote.issued_by_user_id == user_id)
            if older_than:
                query = query.filter(Quote.created_at < older_than)

            for quote in query.all():
                quote.issued_by_user_id = None
                count += 1

        self.db.commit()
        return count

    def _anonymize_audit_trail(
        self, user_id: str, tenant_id: Optional[str] = None
    ) -> int:
        """
        Anonymize audit trail entries.

        CRITICAL: We NEVER delete audit entries.
        We add an anonymization event that references the original
        and indicates the actor has been anonymized.
        """
        from app.core.audit.immutable_ledger import AuditEventImmutable

        events = (
            self.db.query(AuditEventImmutable)
            .filter(AuditEventImmutable.actor_id == user_id)
            .all()
        )

        self.audit.append_event(
            event_type="GDPR",
            action="AUDIT_TRAIL_ANONYMIZED",
            entity_type="audit_anonymization",
            entity_id=str(uuid.uuid4()),
            actor_type="SYSTEM",
            tenant_id=tenant_id,
            payload={
                "original_actor_id": user_id,
                "anonymized_actor_id": "GDPR_ANONYMIZED",
                "event_count": len(events),
                "note": "Original actor identity removed per GDPR erasure request",
            },
        )

        return len(events)

    def _anonymize_user_account(self, user_id: str):
        """Anonymize user account."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            anon_id = hashlib.sha256(str(user_id).encode()).hexdigest()[:12]
            user.email = f"anonymized_{anon_id}@deleted.local"
            if hasattr(user, "status"):
                from app.modules.tenancy.models import UserStatus
                user.status = UserStatus.DISABLED
            self.db.commit()


def create_gdpr_service(
    db: Session,
    audit: ImmutableAuditLedger,
    storage: EvidenceStorage,
) -> GDPRService:
    """Create GDPR service instance."""
    return GDPRService(db, audit, storage)
