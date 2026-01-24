"""
Loss experience tracking models.

Tracks expected vs actual loss for model calibration and pricing validation.
"""

from datetime import date, datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import Column, String, BigInteger, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class LossExperienceRecord(Base):
    """
    Loss experience record.
    
    Tracks expected vs actual loss for each policy to enable:
    - Model calibration
    - Pricing validation
    - Reinsurer reporting
    """
    __tablename__ = 'loss_experience_records'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Tenant
    tenant_id = Column(String(length=26), ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Source references
    policy_id = Column(String(length=26), ForeignKey('policies.id'), nullable=False, index=True)
    claim_id = Column(String(length=26), ForeignKey('claims.id'), nullable=True)
    payout_id = Column(String(length=26), ForeignKey('payouts.id'), nullable=True)
    
    # Dimensions for analysis
    corridor_id = Column(String(length=26), ForeignKey('corridors.id'), nullable=True, index=True)
    carrier_id = Column(String(length=26), ForeignKey('carriers.id'), nullable=True, index=True)
    cargo_type = Column(String(length=100), nullable=True, index=True)
    coverage_type = Column(String(length=50), nullable=True)
    loss_type = Column(String(length=50), nullable=True)  # DAMAGE, LOSS, DELAY, etc.
    
    # Exposure
    exposure_cents = Column(BigInteger(), nullable=False)  # Insured value
    premium_cents = Column(BigInteger(), nullable=False)
    currency = Column(String(length=3), nullable=False, server_default='USD')
    
    # Expected loss (from underwriting)
    expected_loss_cents = Column(BigInteger(), nullable=True)
    expected_loss_rate = Column(Float(), nullable=True)  # expected_loss / exposure
    risk_score_at_bind = Column(Float(), nullable=True)
    model_version_id = Column(String(length=26), ForeignKey('risk_model_versions.id'), nullable=True, index=True)
    
    # Actual loss
    actual_loss_cents = Column(BigInteger(), nullable=False, server_default='0')
    actual_loss_rate = Column(Float(), nullable=True)  # actual_loss / exposure
    paid_loss_cents = Column(BigInteger(), nullable=False, server_default='0')
    reserved_loss_cents = Column(BigInteger(), nullable=False, server_default='0')
    
    # Timing
    policy_effective_date = Column(Date(), nullable=False, index=True)
    loss_date = Column(Date(), nullable=True)
    reported_date = Column(Date(), nullable=True)
    settled_date = Column(Date(), nullable=True)
    
    # Status
    record_status = Column(String(length=20), nullable=False, server_default='ACTIVE')
    # ACTIVE, SETTLED, CANCELLED
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    
    # Relationships
    policy = relationship('Policy', foreign_keys=[policy_id], backref='loss_experience_records')
    claim = relationship('Claim', foreign_keys=[claim_id], backref='loss_experience_records')
    payout = relationship('Payout', foreign_keys=[payout_id], backref='loss_experience_records')
    
    def __repr__(self):
        return f"<LossExperienceRecord(id={self.id}, policy_id={self.policy_id}, expected={self.expected_loss_cents}, actual={self.actual_loss_cents})>"
