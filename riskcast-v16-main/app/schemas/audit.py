"""
Audit API Response Schemas
Pydantic schemas for audit log export and verification
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class AuditEventResponse(BaseModel):
    """Response schema for audit event"""
    id: str = Field(..., description="Event ID (UUID)")
    tenant_id: str = Field(..., description="Tenant ID")
    sequence_num: int = Field(..., description="Sequence number")
    prev_hash: Optional[str] = Field(None, description="Previous event hash")
    event_hash: str = Field(..., description="Event hash (SHA256)")
    event_type: str = Field(..., description="Event type")
    entity_type: Optional[str] = Field(None, description="Entity type")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    action: str = Field(..., description="Action performed")
    actor_type: str = Field(..., description="Actor type (USER, SYSTEM, API_KEY)")
    actor_id: Optional[str] = Field(None, description="Actor ID")
    payload_json: Optional[Dict[str, Any]] = Field(None, description="Event payload")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class AuditEventListResponse(BaseModel):
    """Response schema for list of audit events"""
    events: List[AuditEventResponse] = Field(..., description="List of audit events")
    total: int = Field(..., description="Total number of events (may be more than returned)")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")
    
    class Config:
        from_attributes = True


class AuditExportResponse(BaseModel):
    """Response schema for audit chain export"""
    events: List[AuditEventResponse] = Field(..., description="Exported audit events")
    chain_head_hash: Optional[str] = Field(None, description="Latest event hash from chain head")
    chain_verified: bool = Field(..., description="Whether chain verification passed")
    export_timestamp: datetime = Field(..., description="Export timestamp")
    from_sequence: int = Field(..., description="Starting sequence number")
    to_sequence: Optional[int] = Field(None, description="Ending sequence number")
    total_events: int = Field(..., description="Total events in export")
    format: str = Field(..., description="Export format (json, csv)")
    
    class Config:
        from_attributes = True


class ChainVerificationResponse(BaseModel):
    """Response schema for chain verification"""
    valid: bool = Field(..., description="Whether chain is valid")
    event_count: int = Field(..., description="Number of events verified")
    verified_events: int = Field(..., description="Number of events that passed verification")
    first_invalid_sequence: Optional[int] = Field(None, description="First invalid sequence number (if any)")
    errors: List[str] = Field(default_factory=list, description="Verification errors")
    from_sequence: int = Field(..., description="Starting sequence number")
    
    class Config:
        from_attributes = True
