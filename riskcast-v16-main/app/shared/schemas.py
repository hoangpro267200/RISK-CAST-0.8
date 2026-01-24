"""
Shared Pydantic Schemas
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StandardResponse(BaseModel):
    """Standard API response format"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=50, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel):
    """Paginated response format"""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @classmethod
    def create(cls, items: list[Any], total: int, page: int, page_size: int):
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class TimestampMixin(BaseModel):
    """Mixin for timestamps"""
    created_at: datetime
    updated_at: datetime


class TenantScoped(BaseModel):
    """Mixin for tenant-scoped resources"""
    tenant_id: str


class Versioned(BaseModel):
    """Mixin for versioned resources"""
    version: str
    version_created_at: datetime
