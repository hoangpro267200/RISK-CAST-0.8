"""
Identity & Access Schemas
Pydantic schemas for authentication (login, sessions, API keys)
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.modules.identity_access.models import ApiKeyStatus


# Login Schemas
class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (optional)")


class LoginResponse(BaseModel):
    """Schema for login response"""
    session_id: str
    token: str = Field(..., description="Session token (JWT)")
    expires_at: datetime
    user_id: str
    tenant_id: Optional[str] = None


# Session Schemas
class SessionResponse(BaseModel):
    """Schema for session response"""
    id: str
    user_id: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# API Key Schemas
class ApiKeyCreate(BaseModel):
    """Schema for creating an API key"""
    name: str = Field(..., min_length=1, max_length=255, description="API key name")
    scopes: List[str] = Field(default_factory=list, description="List of permission keys")
    expires_at: Optional[datetime] = Field(None, description="Expiration date (optional)")


class ApiKeyResponse(BaseModel):
    """Schema for API key response (without raw key)"""
    id: str
    tenant_id: str
    name: str
    key_prefix: str
    scopes: List[str] = Field(default_factory=list)
    status: ApiKeyStatus
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApiKeyCreateResponse(BaseModel):
    """Schema for API key creation response (includes raw key shown once)"""
    api_key: ApiKeyResponse
    raw_key: str = Field(..., description="Raw API key (shown only once, store securely)")


# Token Schemas
class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: str = Field(..., description="Subject (user ID)")
    tenant_id: Optional[str] = Field(None, description="Tenant ID")
    session_id: str = Field(..., description="Session ID")
    type: str = Field(default="access", description="Token type")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")


class TokenValidationResult(BaseModel):
    """Result of token validation"""
    is_valid: bool
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    error: Optional[str] = None
