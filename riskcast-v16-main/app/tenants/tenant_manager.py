"""
Multi-tenant Management System

Features:
1. Tenant isolation
2. Custom branding
3. Tenant-specific configuration
4. White-label support
5. Resource quotas
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.orm import Session


class TenantStatus(Enum):
    """Tenant status."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"
    TERMINATED = "TERMINATED"


class TenantPlan(Enum):
    """Tenant subscription plans."""
    STARTER = "STARTER"         # Basic features
    PROFESSIONAL = "PROFESSIONAL"  # Full features
    ENTERPRISE = "ENTERPRISE"   # Custom features + white-label


@dataclass
class TenantBranding:
    """Tenant branding configuration."""
    logo_url: Optional[str]
    primary_color: str
    secondary_color: str
    company_name: str
    support_email: str
    support_phone: Optional[str]
    custom_domain: Optional[str]
    favicon_url: Optional[str]
    email_from_name: Optional[str]


@dataclass
class TenantQuotas:
    """Resource quotas for tenant."""
    max_users: int
    max_policies_per_month: int
    max_api_calls_per_day: int
    max_storage_gb: float
    max_webhooks: int


@dataclass
class Tenant:
    """Tenant entity."""
    id: str
    name: str
    slug: str  # URL-safe identifier
    status: TenantStatus
    plan: TenantPlan
    
    # Branding
    branding: TenantBranding
    
    # Quotas
    quotas: TenantQuotas
    
    # Configuration
    settings: Dict[str, Any]
    features: List[str]
    
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Billing
    billing_email: str
    billing_address: Optional[Dict[str, str]]


class TenantManager:
    """
    Manages multi-tenant operations.
    
    Key responsibilities:
    - Tenant CRUD operations
    - Branding management
    - Quota enforcement
    - Feature flags per tenant
    """
    
    # Default quotas by plan
    DEFAULT_QUOTAS = {
        TenantPlan.STARTER: TenantQuotas(
            max_users=5,
            max_policies_per_month=100,
            max_api_calls_per_day=1000,
            max_storage_gb=5.0,
            max_webhooks=3
        ),
        TenantPlan.PROFESSIONAL: TenantQuotas(
            max_users=25,
            max_policies_per_month=1000,
            max_api_calls_per_day=10000,
            max_storage_gb=50.0,
            max_webhooks=10
        ),
        TenantPlan.ENTERPRISE: TenantQuotas(
            max_users=1000,
            max_policies_per_month=100000,
            max_api_calls_per_day=1000000,
            max_storage_gb=500.0,
            max_webhooks=100
        )
    }
    
    # Features by plan
    PLAN_FEATURES = {
        TenantPlan.STARTER: [
            "basic_risk_assessment",
            "quote_management",
            "policy_management",
            "basic_reporting"
        ],
        TenantPlan.PROFESSIONAL: [
            "basic_risk_assessment",
            "advanced_risk_assessment",
            "quote_management",
            "policy_management",
            "claims_management",
            "basic_reporting",
            "advanced_analytics",
            "api_access",
            "webhooks"
        ],
        TenantPlan.ENTERPRISE: [
            "basic_risk_assessment",
            "advanced_risk_assessment",
            "custom_risk_models",
            "quote_management",
            "policy_management",
            "claims_management",
            "basic_reporting",
            "advanced_analytics",
            "custom_reports",
            "api_access",
            "webhooks",
            "white_label",
            "custom_domain",
            "sso",
            "dedicated_support",
            "custom_integrations"
        ]
    }
    
    def __init__(self, db: Session, audit):
        self.db = db
        self.audit = audit
        self.logger = logging.getLogger(__name__)
    
    async def create_tenant(
        self,
        name: str,
        slug: str,
        plan: TenantPlan,
        billing_email: str,
        branding: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """
        Create a new tenant.
        """
        from app.models.tenant_enhanced import TenantModel
        
        # Check slug uniqueness
        existing = self.db.query(TenantModel).filter(
            TenantModel.slug == slug
        ).first()
        
        if existing:
            raise ValueError(f"Tenant slug '{slug}' already exists")
        
        # Build branding
        tenant_branding = TenantBranding(
            logo_url=branding.get("logo_url") if branding else None,
            primary_color=branding.get("primary_color", "#1a73e8") if branding else "#1a73e8",
            secondary_color=branding.get("secondary_color", "#4285f4") if branding else "#4285f4",
            company_name=branding.get("company_name", name) if branding else name,
            support_email=branding.get("support_email", billing_email) if branding else billing_email,
            support_phone=branding.get("support_phone") if branding else None,
            custom_domain=branding.get("custom_domain") if branding else None,
            favicon_url=branding.get("favicon_url") if branding else None,
            email_from_name=branding.get("email_from_name") if branding else None
        )
        
        # Get quotas for plan
        quotas = self.DEFAULT_QUOTAS[plan]
        
        # Get features for plan
        features = self.PLAN_FEATURES[plan]
        
        # Create model
        tenant_model = TenantModel(
            name=name,
            slug=slug,
            status=TenantStatus.ACTIVE.value,
            plan=plan.value,
            
            # Branding
            logo_url=tenant_branding.logo_url,
            primary_color=tenant_branding.primary_color,
            secondary_color=tenant_branding.secondary_color,
            company_name=tenant_branding.company_name,
            support_email=tenant_branding.support_email,
            support_phone=tenant_branding.support_phone,
            custom_domain=tenant_branding.custom_domain,
            favicon_url=tenant_branding.favicon_url,
            email_from_name=tenant_branding.email_from_name,
            
            # Quotas
            max_users=quotas.max_users,
            max_policies_per_month=quotas.max_policies_per_month,
            max_api_calls_per_day=quotas.max_api_calls_per_day,
            max_storage_gb=quotas.max_storage_gb,
            max_webhooks=quotas.max_webhooks,
            
            # Config
            settings_json=settings or {},
            features=features,
            
            # Billing
            billing_email=billing_email
        )
        
        self.db.add(tenant_model)
        self.db.commit()
        self.db.refresh(tenant_model)
        
        # Audit (synchronous)
        if self.audit:
            self.audit.append_event(
                event_type="TENANT",
                action="TENANT_CREATED",
                entity_type="tenant",
                entity_id=str(tenant_model.id),
                actor_type="SYSTEM",
                payload={
                    "name": name,
                    "slug": slug,
                    "plan": plan.value
                },
                tenant_id=str(tenant_model.id)
            )
        
        self.logger.info(f"Created tenant: {name} ({slug})")
        
        return self._to_tenant(tenant_model)
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        from app.models.tenant_enhanced import TenantModel
        
        model = self.db.query(TenantModel).filter(
            TenantModel.id == tenant_id
        ).first()
        
        return self._to_tenant(model) if model else None
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        from app.models.tenant_enhanced import TenantModel
        
        model = self.db.query(TenantModel).filter(
            TenantModel.slug == slug
        ).first()
        
        return self._to_tenant(model) if model else None
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by custom domain."""
        from app.models.tenant_enhanced import TenantModel
        
        model = self.db.query(TenantModel).filter(
            TenantModel.custom_domain == domain,
            TenantModel.status == TenantStatus.ACTIVE.value
        ).first()
        
        return self._to_tenant(model) if model else None
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any]
    ) -> Tenant:
        """Update tenant."""
        from app.models.tenant_enhanced import TenantModel
        
        model = self.db.query(TenantModel).filter(
            TenantModel.id == tenant_id
        ).first()
        
        if not model:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Update allowed fields
        allowed_fields = [
            "name", "status", "plan",
            "logo_url", "primary_color", "secondary_color",
            "company_name", "support_email", "support_phone",
            "custom_domain", "favicon_url", "email_from_name",
            "settings_json"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(model, field, value)
        
        # If plan changed, update quotas and features
        if "plan" in updates:
            new_plan = TenantPlan(updates["plan"])
            quotas = self.DEFAULT_QUOTAS[new_plan]
            model.max_users = quotas.max_users
            model.max_policies_per_month = quotas.max_policies_per_month
            model.max_api_calls_per_day = quotas.max_api_calls_per_day
            model.max_storage_gb = quotas.max_storage_gb
            model.max_webhooks = quotas.max_webhooks
            model.features = self.PLAN_FEATURES[new_plan]
        
        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        
        # Audit (synchronous)
        if self.audit:
            self.audit.append_event(
                event_type="TENANT",
                action="TENANT_UPDATED",
                entity_type="tenant",
                entity_id=tenant_id,
                actor_type="SYSTEM",
                payload={"updates": list(updates.keys())},
                tenant_id=tenant_id
            )
        
        return self._to_tenant(model)
    
    async def update_branding(
        self,
        tenant_id: str,
        branding: Dict[str, Any]
    ) -> Tenant:
        """Update tenant branding."""
        from app.models.tenant_enhanced import TenantModel
        
        model = self.db.query(TenantModel).filter(
            TenantModel.id == tenant_id
        ).first()
        
        if not model:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Update branding fields
        branding_fields = [
            "logo_url", "primary_color", "secondary_color",
            "company_name", "support_email", "support_phone",
            "custom_domain", "favicon_url", "email_from_name"
        ]
        
        for field in branding_fields:
            if field in branding:
                setattr(model, field, branding[field])
        
        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        
        return self._to_tenant(model)
    
    async def check_quota(
        self,
        tenant_id: str,
        resource: str,
        requested: int = 1
    ) -> bool:
        """
        Check if tenant has quota for resource.
        
        Returns True if within quota, False if exceeded.
        """
        from app.models.tenant_enhanced import TenantModel
        from app.modules.tenancy.models import User
        from app.modules.underwriting.models import Policy
        from app.models.webhook import WebhookSubscriptionModel
        from sqlalchemy import func
        from datetime import date
        
        model = self.db.query(TenantModel).filter(
            TenantModel.id == tenant_id
        ).first()
        
        if not model:
            return False
        
        # Get current usage
        usage = await self._get_resource_usage(tenant_id, resource)
        
        # Get limit
        limits = {
            "users": model.max_users,
            "policies_month": model.max_policies_per_month,
            "api_calls_day": model.max_api_calls_per_day,
            "storage_gb": model.max_storage_gb,
            "webhooks": model.max_webhooks
        }
        
        limit = limits.get(resource)
        if limit is None:
            return True  # No limit defined
        
        return (usage + requested) <= limit
    
    async def _get_resource_usage(self, tenant_id: str, resource: str) -> int:
        """Get current resource usage for tenant."""
        from app.modules.tenancy.models import User
        from app.modules.underwriting.models import Policy
        from app.models.webhook import WebhookSubscriptionModel
        from sqlalchemy import func
        from datetime import date
        
        if resource == "users":
            return self.db.query(func.count(User.id)).filter(
                User.tenant_id == tenant_id,
                User.status == "ACTIVE"
            ).scalar() or 0
        
        elif resource == "policies_month":
            month_start = date.today().replace(day=1)
            month_start_dt = datetime.combine(month_start, datetime.min.time())
            return self.db.query(func.count(Policy.id)).filter(
                Policy.tenant_id == tenant_id,
                Policy.created_at >= month_start_dt
            ).scalar() or 0
        
        elif resource == "webhooks":
            return self.db.query(func.count(WebhookSubscriptionModel.id)).filter(
                WebhookSubscriptionModel.tenant_id == tenant_id,
                WebhookSubscriptionModel.is_active == True,
                WebhookSubscriptionModel.deleted_at.is_(None)
            ).scalar() or 0
        
        # API calls would be tracked separately (Redis/time-series DB)
        # Storage would be tracked from S3/storage metrics
        
        return 0
    
    async def has_feature(self, tenant_id: str, feature: str) -> bool:
        """Check if tenant has access to a feature."""
        from app.models.tenant_enhanced import TenantModel
        
        model = self.db.query(TenantModel).filter(
            TenantModel.id == tenant_id
        ).first()
        
        if not model:
            return False
        
        return feature in (model.features or [])
    
    async def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant-specific configuration."""
        from app.models.tenant_enhanced import TenantModel
        
        model = self.db.query(TenantModel).filter(
            TenantModel.id == tenant_id
        ).first()
        
        if not model:
            return {}
        
        return {
            "branding": {
                "logo_url": model.logo_url,
                "primary_color": model.primary_color,
                "secondary_color": model.secondary_color,
                "company_name": model.company_name,
                "support_email": model.support_email,
                "support_phone": model.support_phone,
                "custom_domain": model.custom_domain,
                "favicon_url": model.favicon_url,
                "email_from_name": model.email_from_name
            },
            "features": model.features or [],
            "settings": model.settings_json or {},
            "quotas": {
                "max_users": model.max_users,
                "max_policies_per_month": model.max_policies_per_month,
                "max_api_calls_per_day": model.max_api_calls_per_day,
                "max_storage_gb": model.max_storage_gb,
                "max_webhooks": model.max_webhooks
            }
        }
    
    def _to_tenant(self, model) -> Optional[Tenant]:
        """Convert model to Tenant dataclass."""
        if not model:
            return None
        
        return Tenant(
            id=str(model.id),
            name=model.name,
            slug=model.slug,
            status=TenantStatus(model.status),
            plan=TenantPlan(model.plan),
            branding=TenantBranding(
                logo_url=model.logo_url,
                primary_color=model.primary_color,
                secondary_color=model.secondary_color,
                company_name=model.company_name or model.name,
                support_email=model.support_email or "",
                support_phone=model.support_phone,
                custom_domain=model.custom_domain,
                favicon_url=model.favicon_url,
                email_from_name=model.email_from_name
            ),
            quotas=TenantQuotas(
                max_users=model.max_users,
                max_policies_per_month=model.max_policies_per_month,
                max_api_calls_per_day=model.max_api_calls_per_day,
                max_storage_gb=model.max_storage_gb,
                max_webhooks=model.max_webhooks
            ),
            settings=model.settings_json or {},
            features=model.features or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            billing_email=model.billing_email or "",
            billing_address=model.billing_address_json
        )
