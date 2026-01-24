"""
Audit Ledger Schemas
Pydantic schemas for audit event logging and querying
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from app.modules.audit_ledger.models import ActorType


class AuditContext(BaseModel):
    """Context information for audit events"""
    request_id: Optional[str] = Field(None, description="Request ID for tracing")
    trace_id: Optional[str] = Field(None, description="Distributed trace ID")
    ip: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    route: Optional[str] = Field(None, description="API route")
    method: Optional[str] = Field(None, description="HTTP method")


class AuditEventCreate(BaseModel):
    """Schema for creating an audit event"""
    tenant_id: Optional[str] = Field(None, description="Tenant ID (nullable for platform events)")
    actor_type: ActorType = Field(..., description="Type of actor")
    actor_id: str = Field(..., max_length=100, description="Actor identifier")
    action: str = Field(..., max_length=100, description="Action performed (e.g., 'risk_assessment.created')")
    resource_type: str = Field(..., max_length=100, description="Type of resource (e.g., 'risk_assessment')")
    resource_id: str = Field(..., max_length=100, description="Resource identifier")
    context: AuditContext = Field(default_factory=AuditContext, description="Context information")
    diff: Optional[Dict[str, Any]] = Field(None, description="State changes (optional)")
    occurred_at: Optional[datetime] = Field(None, description="Event timestamp (defaults to now)")


class AuditEventResponse(BaseModel):
    """Schema for audit event response"""
    id: str
    tenant_id: Optional[str] = None
    occurred_at: datetime
    actor_type: ActorType
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    context_json: Optional[Dict[str, Any]] = None
    diff_json: Optional[Dict[str, Any]] = None
    prev_hash: Optional[str] = None
    event_hash: str
    
    class Config:
        from_attributes = True


class AuditEventQuery(BaseModel):
    """Query filters for audit events"""
    tenant_id: Optional[str] = None
    actor_type: Optional[ActorType] = None
    actor_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    start_date: Optional[datetime] = Field(None, description="Start date for time range")
    end_date: Optional[datetime] = Field(None, description="End date for time range")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
    
    @property
    def has_filters(self) -> bool:
        """Check if any filters are set"""
        return any([
            self.actor_type is not None,
            self.actor_id is not None,
            self.action is not None,
            self.resource_type is not None,
            self.resource_id is not None,
            self.start_date is not None,
            self.end_date is not None,
        ])


class AuditChainVerificationResult(BaseModel):
    """Result of chain verification"""
    is_valid: bool
    total_events: int
    invalid_links: List[Dict[str, Any]] = Field(default_factory=list)
    message: str
