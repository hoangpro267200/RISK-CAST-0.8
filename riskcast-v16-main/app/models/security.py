"""
Security compliance models.

Models for security controls, assessments, and remediation plans.
"""

from datetime import date, datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class SecurityControl(Base):
    """
    Security control model.
    
    Represents a security control from a compliance framework.
    """
    __tablename__ = 'security_controls'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Identification
    control_id = Column(String(length=50), nullable=False, unique=True, index=True)
    name = Column(String(length=255), nullable=False)
    description = Column(Text(), nullable=True)
    
    # Classification
    framework = Column(String(length=50), nullable=False, index=True)
    # SOC2, ISO27001, GDPR, PCI_DSS, NIST
    category = Column(String(length=100), nullable=True, index=True)
    subcategory = Column(String(length=100), nullable=True)
    
    # Control details
    control_type = Column(String(length=50), nullable=True)  # PREVENTIVE, DETECTIVE, CORRECTIVE
    implementation_type = Column(String(length=50), nullable=True)  # TECHNICAL, ADMINISTRATIVE, PHYSICAL
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='NOT_IMPLEMENTED', index=True)
    # NOT_IMPLEMENTED, IMPLEMENTED, PARTIALLY_IMPLEMENTED, NOT_APPLICABLE
    
    # Evidence requirements
    evidence_requirements_json = Column(sa.JSON(), nullable=True)
    # {
    #   "required_evidence": ["policy_document", "audit_logs", "config_screenshots"],
    #   "review_frequency": "QUARTERLY"
    # }
    
    # Owner
    owner_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    owner_role = Column(String(length=100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    assessments = relationship('ControlAssessment', back_populates='control', lazy='select', order_by='desc(ControlAssessment.assessment_date)')
    remediation_plans = relationship('ControlRemediationPlan', back_populates='control', lazy='select')
    
    def __repr__(self):
        return f"<SecurityControl(id={self.id}, control_id={self.control_id}, framework={self.framework})>"


class ControlAssessment(Base):
    """
    Control assessment model.
    
    Records assessments of security controls.
    """
    __tablename__ = 'control_assessments'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Foreign key
    control_id = Column(String(length=26), ForeignKey('security_controls.id'), nullable=False, index=True)
    
    # Assessment details
    assessment_date = Column(Date(), nullable=False, index=True)
    assessor_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    assessment_type = Column(String(length=50), nullable=True)  # INTERNAL, EXTERNAL, SELF
    
    # Results
    effectiveness = Column(String(length=20), nullable=False, index=True)
    # EFFECTIVE, PARTIALLY_EFFECTIVE, INEFFECTIVE
    maturity_level = Column(Integer(), nullable=True)  # 1-5
    risk_rating = Column(String(length=20), nullable=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Findings
    findings_json = Column(sa.JSON(), nullable=True)
    # {
    #   "gaps": [...],
    #   "recommendations": [...],
    #   "compensating_controls": [...]
    # }
    
    # Evidence
    evidence_bundle_id = Column(String(length=26), nullable=True)
    evidence_summary = Column(Text(), nullable=True)
    
    # Next assessment
    next_assessment_date = Column(Date(), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    control = relationship('SecurityControl', foreign_keys=[control_id], back_populates='assessments', lazy='select')
    remediation_plans = relationship('ControlRemediationPlan', back_populates='assessment', lazy='select')
    
    def __repr__(self):
        return f"<ControlAssessment(id={self.id}, control_id={self.control_id}, effectiveness={self.effectiveness})>"


class ControlRemediationPlan(Base):
    """
    Control remediation plan model.
    
    Tracks remediation plans for security controls.
    """
    __tablename__ = 'control_remediation_plans'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Foreign keys
    control_id = Column(String(length=26), ForeignKey('security_controls.id'), nullable=False, index=True)
    assessment_id = Column(String(length=26), ForeignKey('control_assessments.id'), nullable=True)
    
    # Plan details
    title = Column(String(length=255), nullable=False)
    description = Column(Text(), nullable=True)
    priority = Column(String(length=20), nullable=True, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='PLANNED', index=True)
    # PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
    
    # Timeline
    target_date = Column(Date(), nullable=True, index=True)
    completion_date = Column(Date(), nullable=True)
    
    # Owner
    owner_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    
    # Actions
    actions_json = Column(sa.JSON(), nullable=True)
    # [
    #   {"action": "...", "owner": "...", "status": "...", "due_date": "..."}
    # ]
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    control = relationship('SecurityControl', foreign_keys=[control_id], back_populates='remediation_plans', lazy='select')
    assessment = relationship('ControlAssessment', foreign_keys=[assessment_id], back_populates='remediation_plans', lazy='select')
    
    def __repr__(self):
        return f"<ControlRemediationPlan(id={self.id}, control_id={self.control_id}, status={self.status})>"
