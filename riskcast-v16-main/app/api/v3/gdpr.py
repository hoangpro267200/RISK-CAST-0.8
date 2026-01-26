"""
GDPR Compliance API Endpoints

Provides:
1. Data export (Right to Portability)
2. Data deletion (Right to Erasure)
3. Consent management
4. Data access requests
5. Processing records
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import json
import logging

from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/gdpr", tags=["GDPR Compliance"])


# ============================================================================
# Enums and Models
# ============================================================================

class RequestType(str, Enum):
    """GDPR request types."""
    ACCESS = "ACCESS"  # Right to access
    EXPORT = "EXPORT"  # Right to portability
    ERASURE = "ERASURE"  # Right to be forgotten
    RECTIFICATION = "RECTIFICATION"  # Right to rectification
    RESTRICTION = "RESTRICTION"  # Right to restriction


class RequestStatus(str, Enum):
    """Request status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class ConsentPurpose(str, Enum):
    """Consent purposes."""
    MARKETING = "MARKETING"
    ANALYTICS = "ANALYTICS"
    THIRD_PARTY_SHARING = "THIRD_PARTY_SHARING"
    PROFILING = "PROFILING"
    AUTOMATED_DECISIONS = "AUTOMATED_DECISIONS"


class DataExportRequest(BaseModel):
    """Data export request."""
    format: str = Field("json", pattern="^(json|csv|xml)$")
    include_quotes: bool = True
    include_policies: bool = True
    include_claims: bool = True
    include_communications: bool = True
    include_analytics: bool = False


class DataDeletionRequest(BaseModel):
    """Data deletion request."""
    reason: str = Field(..., min_length=10, max_length=500)
    confirm_deletion: bool = Field(..., description="Must be true to proceed")
    retain_legal_required: bool = Field(True, description="Retain data required by law")


class ConsentUpdateRequest(BaseModel):
    """Consent update request."""
    consents: Dict[str, bool]  # purpose -> granted


class RectificationRequest(BaseModel):
    """Data rectification request."""
    field: str
    current_value: str
    corrected_value: str
    reason: str


# Response Models
class GDPRRequestResponse(BaseModel):
    """GDPR request response."""
    request_id: str
    request_type: str
    status: str
    created_at: str
    estimated_completion: str
    download_url: Optional[str] = None


class ConsentResponse(BaseModel):
    """Consent status response."""
    purpose: str
    granted: bool
    granted_at: Optional[str] = None
    expires_at: Optional[str] = None


class DataInventoryResponse(BaseModel):
    """Data inventory response."""
    category: str
    data_types: List[str]
    retention_period: str
    legal_basis: str
    processors: List[str]


# ============================================================================
# In-Memory Storage
# ============================================================================

_requests: Dict[str, Dict] = {}
_consents: Dict[str, Dict[str, Dict]] = {}  # user_id -> purpose -> consent
_data_inventory = [
    {
        "category": "Identity Data",
        "data_types": ["Name", "Email", "Phone", "Address"],
        "retention_period": "7 years after contract end",
        "legal_basis": "Contract performance",
        "processors": ["Internal", "Cloud Provider"]
    },
    {
        "category": "Policy Data",
        "data_types": ["Quote history", "Policy details", "Premium payments"],
        "retention_period": "10 years (legal requirement)",
        "legal_basis": "Legal obligation",
        "processors": ["Internal", "Payment processor"]
    },
    {
        "category": "Claims Data",
        "data_types": ["Claim details", "Documents", "Communications"],
        "retention_period": "10 years (legal requirement)",
        "legal_basis": "Legal obligation",
        "processors": ["Internal", "Claims handler"]
    },
    {
        "category": "Analytics Data",
        "data_types": ["Usage patterns", "Preferences", "Risk profiles"],
        "retention_period": "3 years",
        "legal_basis": "Legitimate interest / Consent",
        "processors": ["Internal", "Analytics provider"]
    }
]


# ============================================================================
# Data Export Endpoints
# ============================================================================

@router.post("/export", response_model=GDPRRequestResponse)
async def request_data_export(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Request data export (Right to Portability - GDPR Art. 20).
    
    Exports all personal data in machine-readable format.
    Processing may take up to 30 days as per GDPR.
    """
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    request_id = str(uuid.uuid4())
    
    request_data = {
        "id": request_id,
        "user_id": user_id,
        "type": RequestType.EXPORT.value,
        "status": RequestStatus.PROCESSING.value,
        "format": request.format,
        "include": {
            "quotes": request.include_quotes,
            "policies": request.include_policies,
            "claims": request.include_claims,
            "communications": request.include_communications,
            "analytics": request.include_analytics
        },
        "created_at": datetime.utcnow().isoformat(),
        "estimated_completion": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "completed_at": None,
        "download_url": None
    }
    
    _requests[request_id] = request_data
    
    # Schedule background processing
    background_tasks.add_task(process_export_request, request_id, user_id, request.dict())
    
    logger.info(f"Data export requested: {request_id} for user {user_id}")
    
    return GDPRRequestResponse(
        request_id=request_id,
        request_type=RequestType.EXPORT.value,
        status=RequestStatus.PROCESSING.value,
        created_at=request_data["created_at"],
        estimated_completion=request_data["estimated_completion"]
    )


async def process_export_request(request_id: str, user_id: str, options: dict):
    """Background task to process export request."""
    import asyncio
    
    # Simulate processing time
    await asyncio.sleep(2)
    
    if request_id in _requests:
        _requests[request_id]["status"] = RequestStatus.COMPLETED.value
        _requests[request_id]["completed_at"] = datetime.utcnow().isoformat()
        _requests[request_id]["download_url"] = f"/api/v3/gdpr/export/{request_id}/download"
        
        logger.info(f"Data export completed: {request_id}")


@router.get("/export/{request_id}/download")
async def download_export(
    request_id: str,
    current_user = Depends(get_current_user)
):
    """Download exported data."""
    req = _requests.get(request_id)
    if not req:
        raise HTTPException(404, "Export request not found")
    
    if req["status"] != RequestStatus.COMPLETED.value:
        raise HTTPException(400, f"Export not ready. Status: {req['status']}")
    
    # Generate mock export data
    export_data = {
        "export_id": request_id,
        "exported_at": datetime.utcnow().isoformat(),
        "user_data": {
            "profile": {
                "id": req["user_id"],
                "created_at": "2025-01-01T00:00:00Z"
            },
            "quotes": [] if req["include"]["quotes"] else "not_included",
            "policies": [] if req["include"]["policies"] else "not_included",
            "claims": [] if req["include"]["claims"] else "not_included"
        }
    }
    
    return export_data


# ============================================================================
# Data Deletion Endpoints
# ============================================================================

@router.post("/erasure", response_model=GDPRRequestResponse)
async def request_data_deletion(
    request: DataDeletionRequest,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_user)
):
    """
    Request data deletion (Right to Erasure - GDPR Art. 17).
    
    Also known as "Right to be Forgotten".
    Some data may be retained for legal compliance.
    """
    if not request.confirm_deletion:
        raise HTTPException(400, "Must confirm deletion to proceed")
    
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    request_id = str(uuid.uuid4())
    
    request_data = {
        "id": request_id,
        "user_id": user_id,
        "type": RequestType.ERASURE.value,
        "status": RequestStatus.PROCESSING.value,
        "reason": request.reason,
        "retain_legal_required": request.retain_legal_required,
        "created_at": datetime.utcnow().isoformat(),
        "estimated_completion": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "completed_at": None
    }
    
    _requests[request_id] = request_data
    
    # Schedule background processing
    background_tasks.add_task(process_deletion_request, request_id, user_id)
    
    logger.info(f"Data deletion requested: {request_id} for user {user_id}")
    
    return GDPRRequestResponse(
        request_id=request_id,
        request_type=RequestType.ERASURE.value,
        status=RequestStatus.PROCESSING.value,
        created_at=request_data["created_at"],
        estimated_completion=request_data["estimated_completion"]
    )


async def process_deletion_request(request_id: str, user_id: str):
    """Background task to process deletion request."""
    import asyncio
    
    await asyncio.sleep(2)
    
    if request_id in _requests:
        _requests[request_id]["status"] = RequestStatus.COMPLETED.value
        _requests[request_id]["completed_at"] = datetime.utcnow().isoformat()
        _requests[request_id]["deleted_categories"] = [
            "Marketing preferences",
            "Analytics data",
            "Session history",
            "Cookies consent"
        ]
        _requests[request_id]["retained_categories"] = [
            "Policy records (legal requirement - 10 years)",
            "Claims records (legal requirement - 10 years)",
            "Financial transactions (legal requirement - 7 years)"
        ]
        
        logger.info(f"Data deletion completed: {request_id}")


# ============================================================================
# Consent Management Endpoints
# ============================================================================

@router.get("/consents", response_model=List[ConsentResponse])
async def get_consents(
    current_user = Depends(get_current_user)
):
    """Get current consent status for all purposes."""
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    user_consents = _consents.get(user_id, {})
    
    consents = []
    for purpose in ConsentPurpose:
        consent = user_consents.get(purpose.value, {})
        consents.append(ConsentResponse(
            purpose=purpose.value,
            granted=consent.get("granted", False),
            granted_at=consent.get("granted_at"),
            expires_at=consent.get("expires_at")
        ))
    
    return consents


@router.put("/consents")
async def update_consents(
    request: ConsentUpdateRequest,
    current_user = Depends(get_current_user)
):
    """Update consent preferences."""
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    if user_id not in _consents:
        _consents[user_id] = {}
    
    updated = []
    for purpose, granted in request.consents.items():
        if purpose not in [p.value for p in ConsentPurpose]:
            continue
        
        _consents[user_id][purpose] = {
            "granted": granted,
            "granted_at": datetime.utcnow().isoformat() if granted else None,
            "expires_at": (datetime.utcnow() + timedelta(days=365)).isoformat() if granted else None,
            "updated_at": datetime.utcnow().isoformat()
        }
        updated.append(purpose)
    
    logger.info(f"Consents updated for user {user_id}: {updated}")
    
    return {
        "updated": updated,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/consents/{purpose}/withdraw")
async def withdraw_consent(
    purpose: str,
    current_user = Depends(get_current_user)
):
    """Withdraw consent for a specific purpose."""
    if purpose not in [p.value for p in ConsentPurpose]:
        raise HTTPException(400, f"Invalid purpose: {purpose}")
    
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    if user_id in _consents and purpose in _consents[user_id]:
        _consents[user_id][purpose]["granted"] = False
        _consents[user_id][purpose]["withdrawn_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"Consent withdrawn: {purpose} for user {user_id}")
    
    return {
        "purpose": purpose,
        "granted": False,
        "withdrawn_at": datetime.utcnow().isoformat()
    }


# ============================================================================
# Data Access and Rectification
# ============================================================================

@router.get("/access")
async def request_data_access(
    current_user = Depends(get_current_user)
):
    """
    Request data access (Right to Access - GDPR Art. 15).
    
    Returns summary of all personal data held.
    """
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    return {
        "user_id": user_id,
        "data_categories": [
            {
                "category": "Identity",
                "fields": ["name", "email", "phone", "address"],
                "source": "User registration"
            },
            {
                "category": "Insurance",
                "fields": ["quotes", "policies", "claims"],
                "source": "Service usage"
            },
            {
                "category": "Technical",
                "fields": ["IP addresses", "Device info", "Session data"],
                "source": "Automatic collection"
            }
        ],
        "processing_purposes": [
            "Contract performance",
            "Legal compliance",
            "Legitimate interest"
        ],
        "third_party_recipients": [
            "Cloud infrastructure provider",
            "Payment processor",
            "Analytics provider (with consent)"
        ],
        "retention_periods": {
            "policy_data": "10 years",
            "claims_data": "10 years",
            "analytics_data": "3 years",
            "session_data": "30 days"
        }
    }


@router.post("/rectification")
async def request_rectification(
    request: RectificationRequest,
    current_user = Depends(get_current_user)
):
    """
    Request data rectification (Right to Rectification - GDPR Art. 16).
    """
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    request_id = str(uuid.uuid4())
    
    request_data = {
        "id": request_id,
        "user_id": user_id,
        "type": RequestType.RECTIFICATION.value,
        "status": RequestStatus.PENDING.value,
        "field": request.field,
        "current_value": request.current_value,
        "corrected_value": request.corrected_value,
        "reason": request.reason,
        "created_at": datetime.utcnow().isoformat()
    }
    
    _requests[request_id] = request_data
    
    logger.info(f"Rectification requested: {request_id}")
    
    return {
        "request_id": request_id,
        "status": RequestStatus.PENDING.value,
        "message": "Your rectification request has been submitted for review."
    }


# ============================================================================
# Data Inventory and Processing Records
# ============================================================================

@router.get("/inventory", response_model=List[DataInventoryResponse])
async def get_data_inventory(
    current_user = Depends(get_current_user)
):
    """
    Get data inventory and processing records (GDPR Art. 30).
    """
    return [
        DataInventoryResponse(**item)
        for item in _data_inventory
    ]


@router.get("/requests")
async def get_gdpr_requests(
    status: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get all GDPR requests for current user."""
    user_id = str(current_user.id) if hasattr(current_user, 'id') else "unknown"
    
    requests = []
    for req in _requests.values():
        if req["user_id"] == user_id:
            if status and req["status"] != status:
                continue
            requests.append({
                "id": req["id"],
                "type": req["type"],
                "status": req["status"],
                "created_at": req["created_at"]
            })
    
    return {"requests": requests}


@router.get("/requests/{request_id}")
async def get_gdpr_request(
    request_id: str,
    current_user = Depends(get_current_user)
):
    """Get GDPR request details."""
    req = _requests.get(request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    
    return req


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def gdpr_health():
    """Check GDPR service health."""
    return {
        "status": "healthy",
        "pending_requests": sum(1 for r in _requests.values() if r["status"] == RequestStatus.PENDING.value),
        "processing_requests": sum(1 for r in _requests.values() if r["status"] == RequestStatus.PROCESSING.value),
        "consent_records": sum(len(c) for c in _consents.values())
    }
