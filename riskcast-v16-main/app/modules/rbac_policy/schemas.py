"""
RBAC & Policy Schemas
Pydantic schemas for role-based access control
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PermissionBase(BaseModel):
    """Base permission schema"""
    name: str
    resource: str
    action: str
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    """Schema for creating a permission"""
    pass


class PermissionResponse(PermissionBase):
    """Schema for permission response"""
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    """Base role schema"""
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a role"""
    permission_ids: List[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    """Schema for updating a role"""
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[str]] = None


class RoleResponse(RoleBase):
    """Schema for role response"""
    id: str
    permissions: List[PermissionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AssignRoleRequest(BaseModel):
    """Schema for assigning role to user"""
    role_id: str
    expires_at: Optional[datetime] = None
