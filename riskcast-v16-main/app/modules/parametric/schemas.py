"""
Parametric Schemas
Pydantic schemas for parametric insurance
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TriggerType(str, Enum):
    """Parametric trigger types"""
    WEATHER = "weather"
    PORT_CONGESTION = "port_congestion"
    NATCAT = "natcat"
    DELAY = "delay"


class TriggerStatus(str, Enum):
    """Trigger status"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ParametricTriggerCreate(BaseModel):
    """Schema for creating parametric trigger"""
    policy_id: str
    trigger_type: TriggerType
    threshold: float
    location: Dict[str, Any]
    trigger_config: Dict[str, Any]
    payout_structure: Optional[Dict[str, Any]] = None
    max_payout_usd: Optional[float] = None
    expires_at: Optional[datetime] = None


class ParametricTriggerResponse(BaseModel):
    """Schema for parametric trigger response"""
    id: str
    trigger_id: str
    policy_id: str
    tenant_id: str
    trigger_type: TriggerType
    status: TriggerStatus
    threshold: float
    location: Dict[str, Any]
    monitoring_enabled: bool
    triggered_at: Optional[datetime] = None
    trigger_value: Optional[float] = None
    payout_amount_usd: Optional[float] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
