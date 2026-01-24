"""
Tenancy Schemas
Pydantic schemas for tenant, user, membership, role, and permission management
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from app.modules.tenancy.models import (
    TenantStatus, UserStatus, MembershipStatus, RoleScope
)


# Tenant Schemas
class TenantCreate(BaseModel):
    """Schema for creating a tenant"""
    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    status: Optional[TenantStatus] = Field(default=TenantStatus.ACTIVE, description="Tenant status")
    subscription_tier: Optional[str] = Field(None, max_length=100, description="Subscription tier")
    features_json: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Feature flags")


class TenantUpdate(BaseModel):
    """Schema for updating a tenant"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[TenantStatus] = None
    subscription_tier: Optional[str] = Field(None, max_length=100)
    features_json: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    """Schema for tenant response"""
    id: str
    name: str
    status: TenantStatus
    subscription_tier: Optional[str] = None
    features_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# User Schemas
class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Plain text password (will be hashed)")
    status: Optional[UserStatus] = Field(default=UserStatus.ACTIVE, description="User status")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, description="New password (will be hashed)")
    status: Optional[UserStatus] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserResponse(BaseModel):
    """Schema for user response (without password)"""
    id: str
    email: str
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Membership Schemas
class MembershipCreate(BaseModel):
    """Schema for creating a membership"""
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    role_id: str = Field(..., description="Role ID")
    status: Optional[MembershipStatus] = Field(default=MembershipStatus.INVITED, description="Membership status")


class MembershipResponse(BaseModel):
    """Schema for membership response"""
    id: str
    tenant_id: str
    user_id: str
    role_id: str
    status: MembershipStatus
    created_at: datetime
    updated_at: datetime
    
    # Optional nested objects
    tenant: Optional[TenantResponse] = None
    user: Optional[UserResponse] = None
    role: Optional['RoleResponse'] = None
    
    class Config:
        from_attributes = True


# Role Schemas
class RoleResponse(BaseModel):
    """Schema for role response"""
    id: str
    name: str
    scope: RoleScope
    created_at: datetime
    updated_at: datetime
    
    # Optional: include permissions
    permissions: Optional[List['PermissionResponse']] = None
    
    class Config:
        from_attributes = True


# Permission Schemas
class PermissionResponse(BaseModel):
    """Schema for permission response"""
    id: str
    key: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Update forward references
MembershipResponse.model_rebuild()
RoleResponse.model_rebuild()


# Additional schemas for queries
class TenantFilters(BaseModel):
    """Filters for listing tenants"""
    status: Optional[TenantStatus] = None
    subscription_tier: Optional[str] = None
    search: Optional[str] = None  # Search in name


class MembershipWithDetails(MembershipResponse):
    """Membership with full details"""
    tenant: TenantResponse
    user: UserResponse
    role: RoleResponse
