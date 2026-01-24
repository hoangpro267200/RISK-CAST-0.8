"""
Audit Ledger Utilities
Helper functions for hash calculation and chain management
RISKCAST V3 - Modular Monolith
"""
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime

from app.shared.utils import generate_ulid


def calculate_event_hash(
    tenant_id: Optional[str],
    occurred_at: datetime,
    actor_type: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    context_json: Optional[Dict[str, Any]] = None,
    diff_json: Optional[Dict[str, Any]] = None,
    prev_hash: Optional[str] = None
) -> str:
    """
    Calculate SHA-256 hash of an audit event.
    
    The hash includes all event data plus the previous hash to form a chain.
    
    Args:
        tenant_id: Tenant ID (can be None for platform events)
        occurred_at: Event timestamp
        actor_type: Type of actor
        actor_id: Actor identifier
        action: Action performed
        resource_type: Type of resource
        resource_id: Resource identifier
        context_json: Context information
        diff_json: State changes
        prev_hash: Previous event hash (for chaining)
        
    Returns:
        SHA-256 hash as hex string (64 characters)
    """
    # Build hash data (exclude id and event_hash from calculation)
    hash_data = {
        "tenant_id": tenant_id,
        "occurred_at": occurred_at.isoformat() if isinstance(occurred_at, datetime) else str(occurred_at),
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "context_json": context_json or {},
        "diff_json": diff_json or {},
        "prev_hash": prev_hash,
    }
    
    # Convert to JSON string (sorted keys for consistency)
    hash_string = json.dumps(hash_data, sort_keys=True, default=str)
    
    # Calculate SHA-256 hash
    hash_obj = hashlib.sha256(hash_string.encode('utf-8'))
    return hash_obj.hexdigest()


def create_audit_event_data(
    tenant_id: Optional[str],
    actor_type: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    context_json: Optional[Dict[str, Any]] = None,
    diff_json: Optional[Dict[str, Any]] = None,
    prev_hash: Optional[str] = None,
    occurred_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Create audit event data dictionary with calculated hash.
    
    Args:
        tenant_id: Tenant ID (can be None)
        actor_type: Type of actor
        actor_id: Actor identifier
        action: Action performed
        resource_type: Type of resource
        resource_id: Resource identifier
        context_json: Context information
        diff_json: State changes
        prev_hash: Previous event hash
        occurred_at: Event timestamp (defaults to now)
        
    Returns:
        Dictionary with all event data including id and event_hash
    """
    if occurred_at is None:
        occurred_at = datetime.utcnow()
    
    # Generate ULID
    event_id = generate_ulid()
    
    # Calculate hash
    event_hash = calculate_event_hash(
        tenant_id=tenant_id,
        occurred_at=occurred_at,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        context_json=context_json,
        diff_json=diff_json,
        prev_hash=prev_hash
    )
    
    return {
        "id": event_id,
        "tenant_id": tenant_id,
        "occurred_at": occurred_at,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "context_json": context_json,
        "diff_json": diff_json,
        "prev_hash": prev_hash,
        "event_hash": event_hash,
    }


def verify_chain_integrity(events: list) -> bool:
    """
    Verify integrity of an audit event chain.
    
    Checks that each event's prev_hash matches the previous event's event_hash.
    
    Args:
        events: List of AuditEvent objects in chronological order
        
    Returns:
        True if chain is valid, False otherwise
    """
    if not events:
        return True
    
    for i in range(1, len(events)):
        prev_event = events[i - 1]
        current_event = events[i]
        
        if current_event.prev_hash != prev_event.event_hash:
            return False
    
    return True
