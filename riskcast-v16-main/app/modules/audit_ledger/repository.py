"""
Audit Ledger Repository
Data access layer for audit events with tenant-scoped queries
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List
from datetime import datetime

from app.modules.audit_ledger.models import AuditEvent, AuditChainHead, ActorType
from app.shared.exceptions import NotFoundError


class AuditEventRepository:
    """Repository for audit event data access"""
    
    def create(self, db: Session, event_data: dict) -> AuditEvent:
        """
        Create a new audit event (append-only).
        
        Args:
            db: Database session
            event_data: Dictionary with event data
            
        Returns:
            Created AuditEvent instance
        """
        event = AuditEvent(**event_data)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    def get_chain_head(self, db: Session, tenant_id: Optional[str] = None, 
                       for_update: bool = False) -> Optional[AuditChainHead]:
        """
        Get chain head for a tenant (with optional row lock).
        
        Args:
            db: Database session
            tenant_id: Tenant ID (None for platform-level)
            for_update: If True, use SELECT FOR UPDATE to lock row
            
        Returns:
            AuditChainHead instance or None
        """
        query = db.query(AuditChainHead).filter(AuditChainHead.tenant_id == tenant_id)
        
        if for_update:
            query = query.with_for_update()
        
        return query.first()
    
    def create_or_update_chain_head(self, db: Session, tenant_id: Optional[str], 
                                   last_event_hash: str) -> AuditChainHead:
        """
        Create or update chain head for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID (None for platform-level)
            last_event_hash: Last event hash in chain
            
        Returns:
            AuditChainHead instance
        """
        chain_head = self.get_chain_head(db, tenant_id)
        
        if chain_head:
            chain_head.last_event_hash = last_event_hash
            chain_head.updated_at = datetime.utcnow()
        else:
            chain_head = AuditChainHead(
                tenant_id=tenant_id,
                last_event_hash=last_event_hash
            )
            db.add(chain_head)
        
        db.commit()
        db.refresh(chain_head)
        return chain_head
    
    def get_by_id(self, db: Session, event_id: str, 
                  tenant_id: Optional[str] = None) -> Optional[AuditEvent]:
        """
        Get audit event by ID.
        
        Args:
            db: Database session
            event_id: Event ID
            tenant_id: Optional tenant ID for tenant-scoped query
            
        Returns:
            AuditEvent instance or None
        """
        query = db.query(AuditEvent).filter(AuditEvent.id == event_id)
        
        if tenant_id is not None:
            query = query.filter(AuditEvent.tenant_id == tenant_id)
        
        return query.first()
    
    def list_events(self, db: Session, tenant_id: Optional[str] = None,
                   actor_type: Optional[ActorType] = None,
                   actor_id: Optional[str] = None,
                   action: Optional[str] = None,
                   resource_type: Optional[str] = None,
                   resource_id: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   limit: int = 100,
                   offset: int = 0) -> List[AuditEvent]:
        """
        List audit events with filters (tenant-scoped).
        
        Args:
            db: Database session
            tenant_id: Tenant ID (required for tenant-scoped queries)
            actor_type: Filter by actor type
            actor_id: Filter by actor ID
            action: Filter by action
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Start date for time range
            end_date: End date for time range
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of AuditEvent instances
        """
        query = db.query(AuditEvent)
        
        # Tenant scoping (required)
        if tenant_id is not None:
            query = query.filter(AuditEvent.tenant_id == tenant_id)
        
        # Apply filters
        if actor_type:
            query = query.filter(AuditEvent.actor_type == actor_type)
        
        if actor_id:
            query = query.filter(AuditEvent.actor_id == actor_id)
        
        if action:
            query = query.filter(AuditEvent.action == action)
        
        if resource_type:
            query = query.filter(AuditEvent.resource_type == resource_type)
        
        if resource_id:
            query = query.filter(AuditEvent.resource_id == resource_id)
        
        if start_date:
            query = query.filter(AuditEvent.occurred_at >= start_date)
        
        if end_date:
            query = query.filter(AuditEvent.occurred_at <= end_date)
        
        # Order by occurred_at (chronological)
        query = query.order_by(AuditEvent.occurred_at)
        
        # Pagination
        return query.offset(offset).limit(limit).all()
    
    def get_all_events_for_tenant(self, db: Session, tenant_id: Optional[str] = None) -> List[AuditEvent]:
        """
        Get all events for a tenant (for chain verification).
        
        Args:
            db: Database session
            tenant_id: Tenant ID (None for platform-level)
            
        Returns:
            List of AuditEvent instances in chronological order
        """
        query = db.query(AuditEvent)
        
        if tenant_id is not None:
            query = query.filter(AuditEvent.tenant_id == tenant_id)
        else:
            query = query.filter(AuditEvent.tenant_id.is_(None))
        
        return query.order_by(AuditEvent.occurred_at).all()
    
    def count_events(self, db: Session, tenant_id: Optional[str] = None,
                    **filters) -> int:
        """
        Count audit events with filters.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            **filters: Additional filter criteria
            
        Returns:
            Total count of matching events
        """
        query = db.query(AuditEvent)
        
        if tenant_id is not None:
            query = query.filter(AuditEvent.tenant_id == tenant_id)
        
        # Apply additional filters
        if filters.get("actor_type"):
            query = query.filter(AuditEvent.actor_type == filters["actor_type"])
        
        if filters.get("action"):
            query = query.filter(AuditEvent.action == filters["action"])
        
        if filters.get("resource_type"):
            query = query.filter(AuditEvent.resource_type == filters["resource_type"])
        
        if filters.get("start_date"):
            query = query.filter(AuditEvent.occurred_at >= filters["start_date"])
        
        if filters.get("end_date"):
            query = query.filter(AuditEvent.occurred_at <= filters["end_date"])
        
        return query.count()
