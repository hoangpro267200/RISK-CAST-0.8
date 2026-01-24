"""
Premium allocation models.

Tracks multi-party premium splits for policies.
"""

from datetime import date, datetime
from typing import Optional, Dict, Any, List
import sqlalchemy as sa
from sqlalchemy import Column, String, BigInteger, Date, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class PremiumAllocationRule(Base):
    """
    Premium allocation rule.
    
    Defines how premiums should be split among parties (insurer, reinsurer, broker, etc.)
    for a given scope (corridor, product, carrier, or default).
    """
    __tablename__ = 'premium_allocation_rules'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Tenant
    tenant_id = Column(String(length=26), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Identification
    name = Column(String(length=255), nullable=False)
    description = Column(Text(), nullable=True)
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='ACTIVE')
    # ACTIVE, INACTIVE
    
    # Scope
    scope_type = Column(String(length=50), nullable=True)  # CORRIDOR, PRODUCT, CARRIER, DEFAULT
    scope_id = Column(String(length=26), nullable=True)
    
    # Allocation parties
    allocations_json = Column(JSON(), nullable=False)
    # [
    #   {"party_type": "INSURER", "party_id": "...", "share_pct": 70, "commission_pct": 0},
    #   {"party_type": "REINSURER", "party_id": "...", "share_pct": 25, "commission_pct": 5},
    #   {"party_type": "BROKER", "party_id": "...", "share_pct": 0, "commission_pct": 5}
    # ]
    
    # Effective dates
    effective_from = Column(Date(), nullable=False)
    effective_to = Column(Date(), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    created_by_user_id = Column(String(length=26), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    # Note: User relationship commented out to avoid circular dependency
    # created_by_user = relationship('User', foreign_keys=[created_by_user_id], lazy='select')
    allocations = relationship(
        'PremiumAllocation',
        foreign_keys='PremiumAllocation.rule_id',
        back_populates='rule',
        lazy='dynamic'
    )
    
    __table_args__ = (
        Index('idx_alloc_rules_scope', 'scope_type', 'scope_id'),
        Index('idx_alloc_rules_effective', 'effective_from', 'effective_to'),
    )
    
    def __repr__(self):
        return f"<PremiumAllocationRule(id={self.id}, name={self.name}, scope={self.scope_type})>"


class PremiumAllocation(Base):
    """
    Premium allocation record.
    
    Tracks the actual premium split for a specific policy.
    """
    __tablename__ = 'premium_allocations'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Tenant
    tenant_id = Column(String(length=26), ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Policy reference
    policy_id = Column(String(length=26), ForeignKey('policies.id', ondelete='RESTRICT'), nullable=False, index=True)
    rule_id = Column(String(length=26), ForeignKey('premium_allocation_rules.id', ondelete='SET NULL'), nullable=True)
    
    # Total premium
    total_premium_cents = Column(BigInteger(), nullable=False)
    currency = Column(String(length=3), nullable=False, server_default='USD')
    
    # Allocations
    allocations_json = Column(JSON(), nullable=False)
    # [
    #   {
    #     "party_type": "INSURER",
    #     "party_id": "...",
    #     "party_name": "...",
    #     "premium_share_cents": 70000,
    #     "commission_cents": 0,
    #     "net_amount_cents": 70000
    #   }
    # ]
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='ALLOCATED')
    # ALLOCATED, SETTLED, RECONCILED
    
    # Settlement tracking
    settlements_json = Column(JSON(), nullable=True)
    # [
    #   {"party_id": "...", "amount_cents": 70000, "settled_at": "...", "reference": "...", "settled_by": "..."}
    # ]
    
    # Timestamps
    allocated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    settled_at = Column(DateTime(), nullable=True)
    
    # Relationships
    policy = relationship(
        'Policy',
        foreign_keys=[policy_id],
        lazy='select'
    )
    rule = relationship(
        'PremiumAllocationRule',
        foreign_keys=[rule_id],
        back_populates='allocations',
        lazy='select'
    )
    
    __table_args__ = (
        Index('idx_allocations_policy', 'policy_id'),
        Index('idx_allocations_status', 'status'),
    )
    
    def __repr__(self):
        return f"<PremiumAllocation(id={self.id}, policy_id={self.policy_id}, status={self.status})>"
