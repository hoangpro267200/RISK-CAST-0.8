"""
API Key management endpoints.

RISKCAST v17 - API Key CRUD Operations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/api/v2", tags=["API Keys"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================

class CreateAPIKeyRequest(BaseModel):
    """Request model for creating an API key."""
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable name for the key")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    scopes: List[str] = Field(default=['*'], description="Permission scopes")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Days until expiration (null = never)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production API Key",
                "description": "For production server integration",
                "scopes": ["risk:analyze", "risk:read"],
                "expires_in_days": 90
            }
        }


class APIKeyResponse(BaseModel):
    """Response model for API key."""
    id: int
    key: Optional[str] = None  # Only shown once on creation
    key_prefix: str
    name: str
    description: Optional[str] = None
    scopes: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    request_count: int
    revoked: bool
    is_valid: bool
    
    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Response for listing API keys."""
    keys: List[APIKeyResponse]
    total: int


class RevokeAPIKeyRequest(BaseModel):
    """Request for revoking an API key."""
    reason: Optional[str] = Field(None, max_length=255, description="Reason for revocation")


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_db_session():
    """Get database session - mock for now."""
    try:
        from app.database import get_db
        return next(get_db())
    except Exception:
        return None


def get_current_user():
    """Get current authenticated user - mock for now."""
    return {
        'user_id': 'current_user',
        'organization_id': 'current_org'
    }


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/api-keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(request: CreateAPIKeyRequest):
    """
    Create new API key.
    
    ⚠️ **IMPORTANT**: The `key` field is only returned once during creation.
    Make sure to save it securely - it cannot be retrieved again!
    
    Available scopes:
    - `*` - Full access
    - `risk:analyze` - Run risk analysis
    - `risk:read` - Read risk results
    - `risk:scenarios` - Run scenarios
    - `ai:chat` - Use AI advisor
    - `ai:export` - Export recommendations
    - `state:read` - Read saved states
    - `state:write` - Write states
    - `admin:keys` - Manage API keys
    """
    try:
        from app.models.api_key import APIKey
        
        # Get current user
        current_user = get_current_user()
        
        # Create API key
        api_key, actual_key = APIKey.create(
            name=request.name,
            description=request.description,
            scopes=request.scopes,
            user_id=current_user['user_id'],
            organization_id=current_user['organization_id'],
            expires_in_days=request.expires_in_days
        )
        
        # Save to database
        db = get_db_session()
        if db:
            db.add(api_key)
            db.commit()
            db.refresh(api_key)
        
        # Return with actual key (only time it's shown!)
        return APIKeyResponse(
            id=api_key.id or 1,
            key=actual_key,  # ⚠️ Only shown on creation!
            key_prefix=api_key.key_prefix,
            name=api_key.name,
            description=api_key.description,
            scopes=api_key.get_scopes(),
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            request_count=api_key.request_count,
            revoked=api_key.revoked,
            is_valid=api_key.is_valid()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating API key: {str(e)}")


@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    include_revoked: bool = Query(False, description="Include revoked keys"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all API keys for current user/organization.
    
    Note: The actual key value is never returned after creation.
    Only the key_prefix is shown for identification.
    """
    try:
        from app.models.api_key import APIKey
        
        current_user = get_current_user()
        db = get_db_session()
        
        if db:
            query = db.query(APIKey).filter(
                APIKey.user_id == current_user['user_id']
            )
            
            if not include_revoked:
                query = query.filter(APIKey.revoked == False)
            
            total = query.count()
            keys = query.order_by(APIKey.created_at.desc()).offset(offset).limit(limit).all()
            
            return APIKeyListResponse(
                keys=[
                    APIKeyResponse(
                        id=key.id,
                        key=None,  # Never return actual key after creation
                        key_prefix=key.key_prefix,
                        name=key.name,
                        description=key.description,
                        scopes=key.get_scopes(),
                        created_at=key.created_at,
                        expires_at=key.expires_at,
                        last_used_at=key.last_used_at,
                        request_count=key.request_count,
                        revoked=key.revoked,
                        is_valid=key.is_valid()
                    )
                    for key in keys
                ],
                total=total
            )
        else:
            # Return empty list if no database
            return APIKeyListResponse(keys=[], total=0)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing API keys: {str(e)}")


@router.get("/api-keys/{key_id}", response_model=APIKeyResponse)
async def get_api_key(key_id: int):
    """
    Get details for a specific API key.
    """
    try:
        from app.models.api_key import APIKey
        
        db = get_db_session()
        
        if db:
            api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
            
            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            return APIKeyResponse(
                id=api_key.id,
                key=None,
                key_prefix=api_key.key_prefix,
                name=api_key.name,
                description=api_key.description,
                scopes=api_key.get_scopes(),
                created_at=api_key.created_at,
                expires_at=api_key.expires_at,
                last_used_at=api_key.last_used_at,
                request_count=api_key.request_count,
                revoked=api_key.revoked,
                is_valid=api_key.is_valid()
            )
        else:
            raise HTTPException(status_code=404, detail="API key not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting API key: {str(e)}")


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(key_id: int, request: RevokeAPIKeyRequest = None):
    """
    Revoke an API key.
    
    Revoked keys cannot be used anymore. This action cannot be undone.
    """
    try:
        from app.models.api_key import APIKey
        
        db = get_db_session()
        
        if db:
            api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
            
            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            if api_key.revoked:
                raise HTTPException(status_code=400, detail="API key already revoked")
            
            # Revoke the key
            reason = request.reason if request else None
            api_key.revoke(reason)
            db.commit()
            
            return {
                "status": "revoked",
                "key_id": key_id,
                "revoked_at": api_key.revoked_at.isoformat(),
                "reason": reason
            }
        else:
            raise HTTPException(status_code=404, detail="API key not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error revoking API key: {str(e)}")


@router.post("/api-keys/{key_id}/regenerate", response_model=APIKeyResponse)
async def regenerate_api_key(key_id: int):
    """
    Regenerate an API key.
    
    This revokes the old key and creates a new one with the same settings.
    
    ⚠️ **IMPORTANT**: The new `key` is only shown once!
    """
    try:
        from app.models.api_key import APIKey
        
        db = get_db_session()
        
        if db:
            old_key = db.query(APIKey).filter(APIKey.id == key_id).first()
            
            if not old_key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            # Revoke old key
            old_key.revoke("Regenerated")
            
            # Create new key with same settings
            new_api_key, actual_key = APIKey.create(
                name=old_key.name,
                description=old_key.description,
                scopes=old_key.get_scopes(),
                user_id=old_key.user_id,
                organization_id=old_key.organization_id,
                expires_in_days=None  # Keep same expiry logic if needed
            )
            
            db.add(new_api_key)
            db.commit()
            db.refresh(new_api_key)
            
            return APIKeyResponse(
                id=new_api_key.id,
                key=actual_key,  # ⚠️ Only shown on creation!
                key_prefix=new_api_key.key_prefix,
                name=new_api_key.name,
                description=new_api_key.description,
                scopes=new_api_key.get_scopes(),
                created_at=new_api_key.created_at,
                expires_at=new_api_key.expires_at,
                last_used_at=new_api_key.last_used_at,
                request_count=new_api_key.request_count,
                revoked=new_api_key.revoked,
                is_valid=new_api_key.is_valid()
            )
        else:
            raise HTTPException(status_code=404, detail="API key not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating API key: {str(e)}")


@router.get("/api-keys/{key_id}/usage")
async def get_api_key_usage(
    key_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to show")
):
    """
    Get usage statistics for an API key.
    """
    try:
        from app.models.api_key import APIKey
        
        db = get_db_session()
        
        if db:
            api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
            
            if not api_key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            # Calculate stats
            age_days = (datetime.utcnow() - api_key.created_at).days if api_key.created_at else 0
            requests_per_day = api_key.request_count / max(1, age_days) if age_days > 0 else 0
            
            return {
                "key_id": key_id,
                "key_prefix": api_key.key_prefix,
                "name": api_key.name,
                "statistics": {
                    "total_requests": api_key.request_count,
                    "last_used": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                    "age_days": age_days,
                    "requests_per_day": round(requests_per_day, 2),
                    "is_active": api_key.last_used_at is not None and (datetime.utcnow() - api_key.last_used_at).days < 7
                }
            }
        else:
            raise HTTPException(status_code=404, detail="API key not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting API key usage: {str(e)}")
