"""
Audit Ledger Service
Business logic for append-only, hash-chained audit logging
RISKCAST V3 - Modular Monolith
"""
import hashlib
import json
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from app.modules.audit_ledger.repository import AuditEventRepository
from app.modules.audit_ledger.models import AuditEvent, AuditChainHead, ActorType
from app.modules.audit_ledger.schemas import (
    AuditEventCreate, AuditEventResponse, AuditEventQuery, AuditContext,
    AuditChainVerificationResult
)
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class AuditLedgerService:
    """Service for audit event logging with hash-chaining"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditEventRepository()
    
    def _canonicalize_json(self, data: dict) -> str:
        """
        Stable JSON serialization for hashing.
        
        Uses consistent formatting to ensure same data produces same hash.
        
        Args:
            data: Dictionary to serialize
            
        Returns:
            Canonical JSON string
        """
        return json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)
    
    def _compute_event_hash(self, event_data: dict, prev_hash: Optional[str] = None) -> str:
        """
        Compute SHA256 hash of event including prev_hash.
        
        Args:
            event_data: Dictionary with event data
            prev_hash: Previous event hash (None for first event)
            
        Returns:
            SHA-256 hash as hex string (64 characters)
        """
        # Normalize occurred_at to ISO format with Z suffix
        occurred_at = event_data['occurred_at']
        if isinstance(occurred_at, datetime):
            occurred_at_str = occurred_at.isoformat() + 'Z'
        else:
            occurred_at_str = str(occurred_at)
        
        # Build hash payload
        hash_payload = {
            'tenant_id': str(event_data['tenant_id']) if event_data.get('tenant_id') else None,
            'occurred_at': occurred_at_str,
            'actor_type': event_data['actor_type'],
            'actor_id': event_data['actor_id'],
            'action': event_data['action'],
            'resource_type': event_data['resource_type'],
            'resource_id': event_data['resource_id'],
            'context_json': event_data.get('context_json') or {},
            'diff_json': event_data.get('diff_json') or {},
            'prev_hash': prev_hash,
        }
        
        # Canonicalize and hash
        canonical = self._canonicalize_json(hash_payload)
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    async def log_event(
        self,
        tenant_id: Optional[str],
        actor_type: ActorType,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        context: AuditContext,
        diff: Optional[Dict[str, Any]] = None,
        occurred_at: Optional[datetime] = None
    ) -> AuditEvent:
        """
        Log audit event with hash-chaining.
        
        Uses SELECT FOR UPDATE on audit_chain_heads to ensure chain integrity.
        All operations are performed in a single transaction.
        
        Args:
            tenant_id: Tenant ID (None for platform events)
            actor_type: Type of actor
            actor_id: Actor identifier
            action: Action performed
            resource_type: Type of resource
            resource_id: Resource identifier
            context: Context information
            diff: State changes (optional)
            occurred_at: Event timestamp (defaults to now)
            
        Returns:
            Created AuditEvent instance
        """
        if occurred_at is None:
            occurred_at = datetime.utcnow()
        
        # 1. Lock chain head for tenant (SELECT FOR UPDATE)
        chain_head = self.repo.get_chain_head(self.db, tenant_id, for_update=True)
        
        # 2. Get prev_hash from chain head (or None if first event)
        prev_hash = chain_head.last_event_hash if chain_head else None
        
        # 3. Prepare event data
        event_data = {
            'id': generate_ulid(),
            'tenant_id': tenant_id,
            'occurred_at': occurred_at,
            'actor_type': actor_type,
            'actor_id': actor_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'context_json': context.dict(exclude_unset=True) if context else None,
            'diff_json': diff,
            'prev_hash': prev_hash,
        }
        
        # 4. Compute event_hash
        event_hash = self._compute_event_hash(event_data, prev_hash)
        event_data['event_hash'] = event_hash
        
        # 5. Insert AuditEvent
        event = self.repo.create(self.db, event_data)
        
        # 6. Update chain head with new hash
        self.repo.create_or_update_chain_head(self.db, tenant_id, event_hash)
        
        logger.info(
            f"Logged audit event: {action} on {resource_type}/{resource_id} "
            f"by {actor_type}/{actor_id} (tenant: {tenant_id})"
        )
        
        return event
    
    async def query_events(
        self,
        tenant_id: Optional[str],
        filters: AuditEventQuery
    ) -> List[AuditEvent]:
        """
        Query audit events with filters.
        
        Args:
            tenant_id: Tenant ID (required for tenant-scoped queries)
            filters: Query filters
            
        Returns:
            List of AuditEvent instances
        """
        events = self.repo.list_events(
            db=self.db,
            tenant_id=tenant_id or filters.tenant_id,
            actor_type=filters.actor_type,
            actor_id=filters.actor_id,
            action=filters.action,
            resource_type=filters.resource_type,
            resource_id=filters.resource_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            limit=filters.limit,
            offset=filters.offset
        )
        
        return events
    
    async def verify_chain(self, tenant_id: Optional[str] = None) -> AuditChainVerificationResult:
        """
        Verify hash chain integrity for a tenant.
        
        Loads all events ordered by occurred_at, recomputes hashes,
        and verifies that each event's prev_hash matches the previous event's event_hash.
        
        Args:
            tenant_id: Tenant ID (None for platform-level chain)
            
        Returns:
            AuditChainVerificationResult with verification status
        """
        # Load all events ordered by occurred_at
        events = self.repo.get_all_events_for_tenant(self.db, tenant_id)
        
        if not events:
            return AuditChainVerificationResult(
                is_valid=True,
                total_events=0,
                message="No events found for tenant"
            )
        
        invalid_links = []
        
        # Verify chain
        for i in range(len(events)):
            event = events[i]
            
            # Get expected prev_hash
            if i == 0:
                # First event should have prev_hash = None
                expected_prev_hash = None
            else:
                # Subsequent events should have prev_hash = previous event's event_hash
                expected_prev_hash = events[i - 1].event_hash
            
            # Check prev_hash
            if event.prev_hash != expected_prev_hash:
                invalid_links.append({
                    "event_id": event.id,
                    "occurred_at": event.occurred_at.isoformat(),
                    "expected_prev_hash": expected_prev_hash,
                    "actual_prev_hash": event.prev_hash,
                    "position": i
                })
            
            # Recompute hash and verify
            event_data = {
                'tenant_id': event.tenant_id,
                'occurred_at': event.occurred_at,
                'actor_type': event.actor_type,
                'actor_id': event.actor_id,
                'action': event.action,
                'resource_type': event.resource_type,
                'resource_id': event.resource_id,
                'context_json': event.context_json,
                'diff_json': event.diff_json,
            }
            
            computed_hash = self._compute_event_hash(event_data, event.prev_hash)
            
            if computed_hash != event.event_hash:
                invalid_links.append({
                    "event_id": event.id,
                    "occurred_at": event.occurred_at.isoformat(),
                    "expected_hash": computed_hash,
                    "actual_hash": event.event_hash,
                    "position": i,
                    "issue": "hash_mismatch"
                })
        
        is_valid = len(invalid_links) == 0
        
        return AuditChainVerificationResult(
            is_valid=is_valid,
            total_events=len(events),
            invalid_links=invalid_links,
            message=f"Chain verification {'passed' if is_valid else 'failed'}: {len(invalid_links)} invalid link(s)"
        )
    
    async def get_event(self, event_id: str, tenant_id: Optional[str] = None) -> AuditEvent:
        """
        Get audit event by ID.
        
        Args:
            event_id: Event ID
            tenant_id: Optional tenant ID for tenant-scoped query
            
        Returns:
            AuditEvent instance
            
        Raises:
            NotFoundError: If event not found
        """
        event = self.repo.get_by_id(self.db, event_id, tenant_id)
        if not event:
            from app.shared.exceptions import NotFoundError
            raise NotFoundError("AuditEvent", event_id)
        return event
    
    async def get_chain_head(self, tenant_id: Optional[str] = None) -> Optional[AuditChainHead]:
        """
        Get chain head for a tenant.
        
        Args:
            tenant_id: Tenant ID (None for platform-level)
            
        Returns:
            AuditChainHead instance or None
        """
        return self.repo.get_chain_head(self.db, tenant_id)
