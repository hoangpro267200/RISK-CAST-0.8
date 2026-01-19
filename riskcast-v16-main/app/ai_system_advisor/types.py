"""
Type definitions for AI System Advisor
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """Chat message"""
    role: Literal['user', 'assistant', 'system']
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Conversation:
    """Conversation session"""
    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message]
    context: Optional[Dict[str, Any]] = None


@dataclass
class SystemContext:
    """System context for AI advisor"""
    session_id: str
    current_assessment: Optional[Dict[str, Any]] = None
    shipment: Optional[Dict[str, Any]] = None
    financial_metrics: Optional[Dict[str, Any]] = None
    esg_metrics: Optional[Dict[str, Any]] = None
    scenario_results: Optional[Dict[str, Any]] = None
    historical_data: Optional[List[Dict[str, Any]]] = None
    available_actions: List[str] = None


@dataclass
class FunctionCall:
    """Function call from LLM"""
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None


@dataclass
class FunctionResult:
    """Function execution result"""
    function_name: str
    success: bool
    result: Any
    error: Optional[str] = None


@dataclass
class AdvisorResponse:
    """AI advisor response"""
    reply: str
    session_id: str
    actions: List[Dict[str, Any]]
    function_calls: List[FunctionResult]
    metadata: Dict[str, Any]


@dataclass
class Recommendation:
    """Risk mitigation recommendation"""
    title: str
    description: str
    risk_reduction: float
    cost_impact: float
    feasibility: float
    priority: int
    category: str


@dataclass
class ActionSuggestion:
    """Suggested action"""
    type: Literal['suggestion', 'required']
    action: str
    label: str
    description: str
    parameters: Optional[Dict[str, Any]] = None
