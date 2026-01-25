"""
Enhanced Tenant Database Model

Extends base tenant model with enterprise features:
- Branding configuration
- Resource quotas
- Plan management
- Custom domains
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Index

from app.database import Base
from app.shared.models import BaseMixin


class TenantModel(Base, BaseMixin):
    """
    Enhanced tenant model with enterprise features.
    
    Extends base tenant with:
    - Branding configuration
    - Resource quotas
    - Plan-based features
    - Custom domain support
    """
    __tablename__ = "tenants_enhanced"
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, server_default="ACTIVE", index=True)
    plan = Column(String(20), nullable=False, server_default="STARTER", index=True)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), server_default="#1a73e8", nullable=False)
    secondary_color = Column(String(7), server_default="#4285f4", nullable=False)
    company_name = Column(String(200), nullable=True)
    support_email = Column(String(200), nullable=True)
    support_phone = Column(String(50), nullable=True)
    custom_domain = Column(String(200), unique=True, nullable=True, index=True)
    favicon_url = Column(String(500), nullable=True)
    email_from_name = Column(String(100), nullable=True)
    
    # Resource quotas
    max_users = Column(Integer, server_default="5", nullable=False)
    max_policies_per_month = Column(Integer, server_default="100", nullable=False)
    max_api_calls_per_day = Column(Integer, server_default="1000", nullable=False)
    max_storage_gb = Column(Float, server_default="5.0", nullable=False)
    max_webhooks = Column(Integer, server_default="3", nullable=False)
    
    # Configuration
    settings_json = Column(JSON, nullable=True, default=dict)
    features = Column(JSON, nullable=True, default=list)  # List of enabled features
    
    # Billing
    billing_email = Column(String(200), nullable=True)
    billing_address_json = Column(JSON, nullable=True)
    
    __table_args__ = (
        Index("ix_tenants_enhanced_slug", "slug"),
        Index("ix_tenants_enhanced_status", "status"),
        Index("ix_tenants_enhanced_plan", "plan"),
        Index("ix_tenants_enhanced_custom_domain", "custom_domain"),
    )
    
    def __repr__(self):
        return f"<TenantModel(id={self.id}, name={self.name}, slug={self.slug}, plan={self.plan})>"
