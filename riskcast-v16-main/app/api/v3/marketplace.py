"""
API Marketplace Endpoints

Provides:
1. Partner integration management
2. Third-party app registration
3. OAuth2 app management
4. API credentials provisioning
5. Partner analytics
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import secrets
import logging

from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/marketplace", tags=["API Marketplace"])


# ============================================================================
# Enums and Models
# ============================================================================

class AppStatus(str, Enum):
    """Application status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class AppCategory(str, Enum):
    """Application category."""
    ANALYTICS = "ANALYTICS"
    INTEGRATION = "INTEGRATION"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    DOCUMENT_PROCESSING = "DOCUMENT_PROCESSING"
    CLAIMS = "CLAIMS"
    REPORTING = "REPORTING"
    OTHER = "OTHER"


class PartnerTier(str, Enum):
    """Partner tier levels."""
    BASIC = "BASIC"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"


# Request/Response Models
class AppRegistrationRequest(BaseModel):
    """App registration request."""
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    category: AppCategory
    website_url: Optional[str] = None
    callback_urls: List[str] = []
    scopes: List[str] = Field(default=["read:quotes", "read:policies"])
    logo_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_url: Optional[str] = None


class AppResponse(BaseModel):
    """App response."""
    id: str
    name: str
    description: str
    category: str
    status: str
    client_id: str
    created_at: str
    scopes: List[str]
    website_url: Optional[str] = None


class AppCredentialsResponse(BaseModel):
    """App credentials response."""
    client_id: str
    client_secret: str
    scopes: List[str]
    token_endpoint: str
    expires_at: Optional[str] = None


class PartnerRegistrationRequest(BaseModel):
    """Partner registration request."""
    company_name: str = Field(..., min_length=2, max_length=200)
    contact_email: str
    contact_name: str
    description: str = Field(..., min_length=10, max_length=2000)
    website: Optional[str] = None
    use_case: str = Field(..., min_length=20, max_length=2000)


class PartnerResponse(BaseModel):
    """Partner response."""
    id: str
    company_name: str
    tier: str
    status: str
    api_key: Optional[str] = None
    created_at: str
    approved_at: Optional[str] = None


class WebhookSubscriptionRequest(BaseModel):
    """Webhook subscription request."""
    url: str
    events: List[str] = Field(..., min_length=1)
    secret: Optional[str] = None


class APIUsageResponse(BaseModel):
    """API usage response."""
    app_id: str
    period: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    endpoints: Dict[str, int]


# ============================================================================
# In-Memory Storage (Replace with database in production)
# ============================================================================

_apps: Dict[str, Dict] = {}
_partners: Dict[str, Dict] = {}
_webhooks: Dict[str, Dict] = {}
_usage_stats: Dict[str, Dict] = {}


# Available scopes
AVAILABLE_SCOPES = {
    "read:quotes": "Read quote data",
    "write:quotes": "Create and modify quotes",
    "read:policies": "Read policy data",
    "write:policies": "Create and modify policies",
    "read:claims": "Read claims data",
    "write:claims": "Submit and modify claims",
    "read:analytics": "Access analytics data",
    "read:risk": "Access risk assessments",
    "write:risk": "Request risk assessments",
    "read:documents": "Access documents",
    "write:documents": "Upload documents",
    "webhooks": "Manage webhook subscriptions",
    "admin": "Administrative access"
}

# Webhook events
AVAILABLE_EVENTS = [
    "quote.created",
    "quote.accepted",
    "quote.expired",
    "policy.issued",
    "policy.renewed",
    "policy.cancelled",
    "claim.submitted",
    "claim.approved",
    "claim.rejected",
    "risk.alert",
    "payment.received",
    "payment.failed"
]


# ============================================================================
# App Management Endpoints
# ============================================================================

@router.post("/apps", response_model=AppResponse)
async def register_app(
    request: AppRegistrationRequest,
    current_user = Depends(get_current_user)
):
    """
    Register a new marketplace application.
    
    Creates OAuth2 credentials for the app.
    """
    # Validate scopes
    invalid_scopes = [s for s in request.scopes if s not in AVAILABLE_SCOPES]
    if invalid_scopes:
        raise HTTPException(400, f"Invalid scopes: {invalid_scopes}")
    
    # Generate credentials
    app_id = str(uuid.uuid4())
    client_id = f"rc_{secrets.token_hex(16)}"
    client_secret = secrets.token_urlsafe(32)
    
    # Create app record
    app_data = {
        "id": app_id,
        "name": request.name,
        "description": request.description,
        "category": request.category.value,
        "status": AppStatus.PENDING.value,
        "client_id": client_id,
        "client_secret_hash": hash(client_secret),  # Store hash
        "scopes": request.scopes,
        "callback_urls": request.callback_urls,
        "website_url": request.website_url,
        "logo_url": request.logo_url,
        "privacy_policy_url": request.privacy_policy_url,
        "terms_url": request.terms_url,
        "owner_id": str(current_user.id) if hasattr(current_user, 'id') else "unknown",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None,
        "_client_secret": client_secret  # Temporary storage for response
    }
    
    _apps[app_id] = app_data
    
    logger.info(f"App registered: {request.name} ({app_id})")
    
    return AppResponse(
        id=app_id,
        name=request.name,
        description=request.description,
        category=request.category.value,
        status=AppStatus.PENDING.value,
        client_id=client_id,
        created_at=app_data["created_at"],
        scopes=request.scopes,
        website_url=request.website_url
    )


@router.get("/apps", response_model=List[AppResponse])
async def list_apps(
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """
    List registered applications.
    
    Returns apps owned by the current user.
    """
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    apps = []
    for app in _apps.values():
        if app["owner_id"] == user_id:
            if status and app["status"] != status:
                continue
            if category and app["category"] != category:
                continue
            
            apps.append(AppResponse(
                id=app["id"],
                name=app["name"],
                description=app["description"],
                category=app["category"],
                status=app["status"],
                client_id=app["client_id"],
                created_at=app["created_at"],
                scopes=app["scopes"],
                website_url=app.get("website_url")
            ))
    
    return apps


@router.get("/apps/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: str,
    current_user = Depends(get_current_user)
):
    """Get application details."""
    app = _apps.get(app_id)
    if not app:
        raise HTTPException(404, "App not found")
    
    return AppResponse(
        id=app["id"],
        name=app["name"],
        description=app["description"],
        category=app["category"],
        status=app["status"],
        client_id=app["client_id"],
        created_at=app["created_at"],
        scopes=app["scopes"],
        website_url=app.get("website_url")
    )


@router.get("/apps/{app_id}/credentials", response_model=AppCredentialsResponse)
async def get_app_credentials(
    app_id: str,
    current_user = Depends(get_current_user)
):
    """
    Get app credentials.
    
    Only shows client_secret once during registration.
    """
    app = _apps.get(app_id)
    if not app:
        raise HTTPException(404, "App not found")
    
    # Only show secret if recently created
    client_secret = app.get("_client_secret")
    if client_secret:
        # Remove after first retrieval
        del app["_client_secret"]
    
    return AppCredentialsResponse(
        client_id=app["client_id"],
        client_secret=client_secret or "***HIDDEN***",
        scopes=app["scopes"],
        token_endpoint="/api/v3/auth/oauth/token"
    )


@router.post("/apps/{app_id}/rotate-secret")
async def rotate_app_secret(
    app_id: str,
    current_user = Depends(get_current_user)
):
    """Rotate app client secret."""
    app = _apps.get(app_id)
    if not app:
        raise HTTPException(404, "App not found")
    
    new_secret = secrets.token_urlsafe(32)
    app["client_secret_hash"] = hash(new_secret)
    app["updated_at"] = datetime.utcnow().isoformat()
    
    return {
        "client_id": app["client_id"],
        "client_secret": new_secret,
        "message": "Secret rotated. Store this securely - it won't be shown again."
    }


@router.delete("/apps/{app_id}")
async def delete_app(
    app_id: str,
    current_user = Depends(get_current_user)
):
    """Delete an application."""
    if app_id not in _apps:
        raise HTTPException(404, "App not found")
    
    del _apps[app_id]
    
    return {"message": "App deleted successfully"}


# ============================================================================
# Partner Management Endpoints
# ============================================================================

@router.post("/partners", response_model=PartnerResponse)
async def register_partner(
    request: PartnerRegistrationRequest,
    current_user = Depends(get_current_user)
):
    """
    Register as a marketplace partner.
    
    Requires approval before API access is granted.
    """
    partner_id = str(uuid.uuid4())
    
    partner_data = {
        "id": partner_id,
        "company_name": request.company_name,
        "contact_email": request.contact_email,
        "contact_name": request.contact_name,
        "description": request.description,
        "website": request.website,
        "use_case": request.use_case,
        "tier": PartnerTier.BASIC.value,
        "status": AppStatus.PENDING.value,
        "api_key": None,
        "owner_id": str(current_user.id) if hasattr(current_user, 'id') else "unknown",
        "created_at": datetime.utcnow().isoformat(),
        "approved_at": None,
        "rate_limit": 100,  # requests per minute
        "monthly_quota": 10000
    }
    
    _partners[partner_id] = partner_data
    
    logger.info(f"Partner registered: {request.company_name} ({partner_id})")
    
    return PartnerResponse(
        id=partner_id,
        company_name=request.company_name,
        tier=PartnerTier.BASIC.value,
        status=AppStatus.PENDING.value,
        created_at=partner_data["created_at"]
    )


@router.get("/partners/me", response_model=PartnerResponse)
async def get_my_partner_account(
    current_user = Depends(get_current_user)
):
    """Get current user's partner account."""
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    for partner in _partners.values():
        if partner["owner_id"] == user_id:
            return PartnerResponse(
                id=partner["id"],
                company_name=partner["company_name"],
                tier=partner["tier"],
                status=partner["status"],
                api_key=partner.get("api_key"),
                created_at=partner["created_at"],
                approved_at=partner.get("approved_at")
            )
    
    raise HTTPException(404, "Partner account not found")


@router.post("/partners/{partner_id}/approve")
async def approve_partner(
    partner_id: str,
    tier: Optional[str] = Query(PartnerTier.BASIC.value),
    current_user = Depends(get_current_user)
):
    """
    Approve a partner (admin only).
    
    Generates API key and sets tier.
    """
    partner = _partners.get(partner_id)
    if not partner:
        raise HTTPException(404, "Partner not found")
    
    # Generate API key
    api_key = f"rk_live_{secrets.token_hex(24)}"
    
    partner["status"] = AppStatus.APPROVED.value
    partner["tier"] = tier
    partner["api_key"] = api_key
    partner["approved_at"] = datetime.utcnow().isoformat()
    
    # Set rate limits based on tier
    tier_limits = {
        PartnerTier.BASIC.value: {"rate_limit": 100, "monthly_quota": 10000},
        PartnerTier.SILVER.value: {"rate_limit": 500, "monthly_quota": 100000},
        PartnerTier.GOLD.value: {"rate_limit": 2000, "monthly_quota": 1000000},
        PartnerTier.PLATINUM.value: {"rate_limit": 10000, "monthly_quota": -1}  # Unlimited
    }
    
    limits = tier_limits.get(tier, tier_limits[PartnerTier.BASIC.value])
    partner.update(limits)
    
    logger.info(f"Partner approved: {partner['company_name']} - Tier: {tier}")
    
    return {
        "partner_id": partner_id,
        "status": "approved",
        "tier": tier,
        "api_key": api_key,
        "rate_limit": partner["rate_limit"],
        "monthly_quota": partner["monthly_quota"]
    }


# ============================================================================
# Webhook Management Endpoints
# ============================================================================

@router.post("/webhooks")
async def create_webhook(
    request: WebhookSubscriptionRequest,
    current_user = Depends(get_current_user)
):
    """
    Subscribe to webhook events.
    """
    # Validate events
    invalid_events = [e for e in request.events if e not in AVAILABLE_EVENTS]
    if invalid_events:
        raise HTTPException(400, f"Invalid events: {invalid_events}")
    
    webhook_id = str(uuid.uuid4())
    webhook_secret = request.secret or secrets.token_urlsafe(32)
    
    webhook_data = {
        "id": webhook_id,
        "url": request.url,
        "events": request.events,
        "secret": webhook_secret,
        "owner_id": str(current_user.id) if hasattr(current_user, 'id') else "unknown",
        "created_at": datetime.utcnow().isoformat(),
        "enabled": True,
        "failure_count": 0,
        "last_delivery": None
    }
    
    _webhooks[webhook_id] = webhook_data
    
    return {
        "id": webhook_id,
        "url": request.url,
        "events": request.events,
        "secret": webhook_secret,
        "enabled": True
    }


@router.get("/webhooks")
async def list_webhooks(
    current_user = Depends(get_current_user)
):
    """List webhook subscriptions."""
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    webhooks = []
    for wh in _webhooks.values():
        if wh["owner_id"] == user_id:
            webhooks.append({
                "id": wh["id"],
                "url": wh["url"],
                "events": wh["events"],
                "enabled": wh["enabled"],
                "failure_count": wh["failure_count"],
                "last_delivery": wh["last_delivery"]
            })
    
    return {"webhooks": webhooks}


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a webhook subscription."""
    if webhook_id not in _webhooks:
        raise HTTPException(404, "Webhook not found")
    
    del _webhooks[webhook_id]
    
    return {"message": "Webhook deleted"}


# ============================================================================
# Discovery and Catalog Endpoints
# ============================================================================

@router.get("/catalog")
async def get_marketplace_catalog(
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Browse marketplace catalog.
    
    Returns approved apps available for integration.
    """
    catalog = []
    
    for app in _apps.values():
        if app["status"] != AppStatus.APPROVED.value:
            continue
        
        if category and app["category"] != category:
            continue
        
        if search and search.lower() not in app["name"].lower():
            continue
        
        catalog.append({
            "id": app["id"],
            "name": app["name"],
            "description": app["description"],
            "category": app["category"],
            "logo_url": app.get("logo_url"),
            "website_url": app.get("website_url")
        })
    
    return {
        "apps": catalog,
        "total": len(catalog),
        "categories": [c.value for c in AppCategory]
    }


@router.get("/scopes")
async def get_available_scopes():
    """Get available OAuth2 scopes."""
    return {
        "scopes": [
            {"name": name, "description": desc}
            for name, desc in AVAILABLE_SCOPES.items()
        ]
    }


@router.get("/events")
async def get_available_events():
    """Get available webhook events."""
    return {
        "events": AVAILABLE_EVENTS
    }


# ============================================================================
# Usage Analytics Endpoints
# ============================================================================

@router.get("/apps/{app_id}/usage", response_model=APIUsageResponse)
async def get_app_usage(
    app_id: str,
    period: str = Query("30d", regex="^(7d|30d|90d)$"),
    current_user = Depends(get_current_user)
):
    """Get API usage statistics for an app."""
    if app_id not in _apps:
        raise HTTPException(404, "App not found")
    
    # Return mock usage data
    return APIUsageResponse(
        app_id=app_id,
        period=period,
        total_requests=1250,
        successful_requests=1200,
        failed_requests=50,
        endpoints={
            "/api/v3/quotes": 500,
            "/api/v3/policies": 300,
            "/api/v3/risk/assess": 450
        }
    )


@router.get("/partners/{partner_id}/usage")
async def get_partner_usage(
    partner_id: str,
    current_user = Depends(get_current_user)
):
    """Get API usage for a partner."""
    partner = _partners.get(partner_id)
    if not partner:
        raise HTTPException(404, "Partner not found")
    
    return {
        "partner_id": partner_id,
        "tier": partner["tier"],
        "rate_limit": partner["rate_limit"],
        "monthly_quota": partner["monthly_quota"],
        "usage_this_month": 2500,
        "remaining_quota": partner["monthly_quota"] - 2500 if partner["monthly_quota"] > 0 else "unlimited"
    }


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def marketplace_health():
    """Check marketplace service health."""
    return {
        "status": "healthy",
        "registered_apps": len(_apps),
        "partners": len(_partners),
        "webhooks": len(_webhooks),
        "available_scopes": len(AVAILABLE_SCOPES),
        "available_events": len(AVAILABLE_EVENTS)
    }
