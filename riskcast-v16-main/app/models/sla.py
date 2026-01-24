"""
SLA monitoring models.

Models for SLA definitions, measurements, and breaches.
"""

from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class SLADefinition(Base):
    """
    SLA definition model.
    
    Defines service level agreements with targets and thresholds.
    """
    __tablename__ = 'sla_definitions'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Tenant (nullable for system-wide SLAs)
    tenant_id = Column(String(length=26), ForeignKey('tenants.id'), nullable=True, index=True)
    
    # Identification
    name = Column(String(length=255), nullable=False)
    description = Column(Text(), nullable=True)
    category = Column(String(length=50), nullable=False, index=True)
    # AVAILABILITY, RESPONSE_TIME, PROCESSING_TIME, DATA_QUALITY
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='ACTIVE', index=True)
    
    # Metrics
    metric_name = Column(String(length=100), nullable=False)
    metric_unit = Column(String(length=50), nullable=True)
    target_value = Column(Float(), nullable=False)
    warning_threshold = Column(Float(), nullable=True)
    critical_threshold = Column(Float(), nullable=True)
    comparison = Column(String(length=10), nullable=False)  # >=, <=, ==
    
    # Measurement
    measurement_window = Column(String(length=20), nullable=True)  # HOURLY, DAILY, WEEKLY, MONTHLY
    measurement_config_json = Column(sa.JSON(), nullable=True)
    
    # Contractual
    contract_reference = Column(String(length=255), nullable=True)
    penalty_config_json = Column(sa.JSON(), nullable=True)
    # {
    #   "penalty_type": "CREDIT",
    #   "penalty_per_violation_pct": 5,
    #   "max_monthly_penalty_pct": 25
    # }
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    measurements = relationship('SLAMeasurement', back_populates='sla_definition', lazy='select')
    breaches = relationship('SLABreach', back_populates='sla_definition', lazy='select')
    
    def __repr__(self):
        return f"<SLADefinition(id={self.id}, name={self.name}, category={self.category})>"


class SLAMeasurement(Base):
    """
    SLA measurement model.
    
    Records actual measurements against SLA definitions.
    """
    __tablename__ = 'sla_measurements'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Foreign keys
    sla_definition_id = Column(String(length=26), ForeignKey('sla_definitions.id'), nullable=False, index=True)
    tenant_id = Column(String(length=26), ForeignKey('tenants.id'), nullable=True)
    
    # Measurement period
    period_start = Column(DateTime(), nullable=False, index=True)
    period_end = Column(DateTime(), nullable=False, index=True)
    
    # Results
    measured_value = Column(Float(), nullable=False)
    target_value = Column(Float(), nullable=False)
    status = Column(String(length=20), nullable=False, index=True)
    # MET, WARNING, BREACHED
    
    # Details
    sample_count = Column(Integer(), nullable=True)
    details_json = Column(sa.JSON(), nullable=True)
    # {
    #   "breakdown": [...],
    #   "outliers": [...],
    #   "notes": "..."
    # }
    
    # Timestamps
    measured_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    sla_definition = relationship('SLADefinition', foreign_keys=[sla_definition_id], back_populates='measurements', lazy='select')
    breaches = relationship('SLABreach', back_populates='measurement', lazy='select')
    
    def __repr__(self):
        return f"<SLAMeasurement(id={self.id}, sla_def_id={self.sla_definition_id}, status={self.status})>"


class SLABreach(Base):
    """
    SLA breach model.
    
    Tracks violations of SLA definitions.
    """
    __tablename__ = 'sla_breaches'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Foreign keys
    sla_definition_id = Column(String(length=26), ForeignKey('sla_definitions.id'), nullable=False, index=True)
    measurement_id = Column(String(length=26), ForeignKey('sla_measurements.id'), nullable=False)
    tenant_id = Column(String(length=26), ForeignKey('tenants.id'), nullable=True)
    
    # Breach details
    severity = Column(String(length=20), nullable=False, index=True)  # WARNING, CRITICAL
    target_value = Column(Float(), nullable=False)
    actual_value = Column(Float(), nullable=False)
    variance = Column(Float(), nullable=False)
    
    # Resolution
    status = Column(String(length=20), nullable=False, server_default='OPEN', index=True)
    # OPEN, ACKNOWLEDGED, RESOLVED, CREDITED
    root_cause = Column(Text(), nullable=True)
    resolution_notes = Column(Text(), nullable=True)
    
    # Penalty
    penalty_applied = Column(Boolean(), nullable=False, server_default='0')
    penalty_amount_cents = Column(Integer(), nullable=True)
    penalty_currency = Column(String(length=3), nullable=True)
    
    # Timestamps
    occurred_at = Column(DateTime(), nullable=False, index=True)
    acknowledged_at = Column(DateTime(), nullable=True)
    acknowledged_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime(), nullable=True)
    resolved_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # Relationships
    sla_definition = relationship('SLADefinition', foreign_keys=[sla_definition_id], back_populates='breaches', lazy='select')
    measurement = relationship('SLAMeasurement', foreign_keys=[measurement_id], back_populates='breaches', lazy='select')
    # Note: User relationship would be defined if User model is available
    # acknowledged_by_user = relationship('User', foreign_keys=[acknowledged_by_user_id], lazy='select')
    # resolved_by_user = relationship('User', foreign_keys=[resolved_by_user_id], lazy='select')
    
    def __repr__(self):
        return f"<SLABreach(id={self.id}, sla_def_id={self.sla_definition_id}, status={self.status}, severity={self.severity})>"
