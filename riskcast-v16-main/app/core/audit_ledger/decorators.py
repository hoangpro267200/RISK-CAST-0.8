"""
Audit Action Decorators
Decorator-based audit logging for service methods
"""
from __future__ import annotations

import functools
from typing import Callable, Optional, Dict, Any
import inspect

from app.core.audit_ledger.ledger import AuditLedger


def audit_action(
    event_type: str,
    action: str,
    entity_type: Optional[str] = None,
    get_entity_id: Optional[Callable] = None,
    get_payload: Optional[Callable] = None,
    get_actor_id: Optional[Callable] = None,
    actor_type: str = "SYSTEM",
):
    """
    Decorator to automatically emit audit events for service methods.
    
    Usage:
        @audit_action(
            event_type="RISK_ASSESSMENT",
            action="CREATED",
            entity_type="risk_assessment",
            get_entity_id=lambda result: result.id,
            get_payload=lambda result: {"input_hash": result.input_hash}
        )
        def create_assessment(self, tenant_id, ...):
            ...
            return assessment
    
    Args:
        event_type: Type of event (e.g., "RISK_ASSESSMENT", "RISK_RUN")
        action: Action performed (e.g., "CREATED", "STARTED", "COMPLETED")
        entity_type: Type of entity (e.g., "risk_assessment", "risk_run")
        get_entity_id: Function to extract entity_id from method result
        get_payload: Function to extract payload from method result/args
        get_actor_id: Function to extract actor_id from method args/kwargs
        actor_type: Type of actor (USER, SYSTEM, API_KEY) - defaults to SYSTEM
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Call original method
            result = func(self, *args, **kwargs)
            
            # Get audit ledger from service instance
            if not hasattr(self, 'audit') or not isinstance(self.audit, AuditLedger):
                # If no audit ledger, skip audit (for backward compatibility)
                return result
            
            # Extract tenant_id from args/kwargs
            tenant_id = kwargs.get('tenant_id')
            if tenant_id is None:
                # Try to get from args by parameter name
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if 'tenant_id' in params:
                    idx = params.index('tenant_id')
                    if idx < len(args):
                        tenant_id = args[idx]
            
            if tenant_id is None:
                # Try to get from result object
                if hasattr(result, 'tenant_id'):
                    tenant_id = result.tenant_id
                elif isinstance(result, tuple) and len(result) > 0:
                    # Handle (result, bool) tuples
                    if hasattr(result[0], 'tenant_id'):
                        tenant_id = result[0].tenant_id
            
            if tenant_id is None:
                # Cannot audit without tenant_id
                return result
            
            # Extract entity_id
            entity_id = None
            if get_entity_id:
                entity_id = get_entity_id(result)
            elif hasattr(result, 'id'):
                entity_id = result.id
            elif isinstance(result, tuple) and len(result) > 0:
                if hasattr(result[0], 'id'):
                    entity_id = result[0].id
            
            # Extract payload
            payload = None
            if get_payload:
                payload = get_payload(result, *args, **kwargs)
            elif hasattr(result, '__dict__'):
                # Default: include relevant fields from result
                payload = {}
                for key in ['input_hash', 'schema_version', 'status', 'result_hash']:
                    if hasattr(result, key):
                        payload[key] = getattr(result, key)
            
            # Extract actor_id
            actor_id = None
            if get_actor_id:
                actor_id = get_actor_id(*args, **kwargs)
            elif 'user_id' in kwargs:
                actor_id = kwargs['user_id']
            elif 'created_by_user_id' in kwargs:
                actor_id = kwargs['created_by_user_id']
            elif hasattr(result, 'created_by_user_id'):
                actor_id = result.created_by_user_id
            
            # Emit audit event
            try:
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type=event_type,
                    action=action,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    actor_type=actor_type,
                    actor_id=actor_id,
                    payload=payload,
                )
            except Exception as e:
                # Log error but don't fail the operation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to emit audit event: {e}")
            
            return result
        
        return wrapper
    return decorator
