"""
Tenant-Scoped Database Session
Automatically filters queries by tenant_id when tenant context is set.
"""
from __future__ import annotations

from typing import Any, Optional, Type, TypeVar
from sqlalchemy.orm import Session, Query
from sqlalchemy.orm.query import Query as SQLAlchemyQuery

from app.core.tenancy.context import get_current_tenant_id, TenantNotSetError

T = TypeVar('T')


class TenantScopedQuery:
    """
    Query wrapper that automatically adds tenant_id filter.
    
    Automatically filters queries by tenant_id when:
    1. Tenant context is set (via tenant_context())
    2. Model has tenant_id attribute
    """
    
    @staticmethod
    def filter_by_tenant(query: Query, model: Type[T]) -> Query:
        """
        Add tenant_id filter to query if model is tenant-scoped.
        
        Args:
            query: SQLAlchemy query object
            model: SQLAlchemy model class
            
        Returns:
            Query with tenant_id filter added (if applicable)
        """
        # Check if model has tenant_id attribute
        if not hasattr(model, 'tenant_id'):
            return query
        
        # Try to get tenant context
        try:
            tenant_id = get_current_tenant_id()
        except TenantNotSetError:
            # No tenant context - return query as-is
            # This allows queries without tenant context (e.g., admin queries)
            return query
        
        # Add tenant_id filter
        return query.filter(model.tenant_id == tenant_id)


class TenantScopedSession(Session):
    """
    SQLAlchemy Session that automatically scopes queries by tenant.
    
    Overrides query() method to automatically add tenant_id filter
    for tenant-scoped models.
    """
    
    def query(self, *entities: Type[T], **kwargs: Any) -> Query:
        """
        Create a query with automatic tenant scoping.
        
        Args:
            *entities: Model classes to query
            **kwargs: Additional query arguments
            
        Returns:
            Query object with tenant_id filter applied (if applicable)
        """
        # Call parent query() method
        query = super().query(*entities, **kwargs)
        
        # Apply tenant scoping to each entity
        for entity in entities:
            query = TenantScopedQuery.filter_by_tenant(query, entity)
        
        return query
    
    def add(self, instance: Any, _warn: bool = True) -> None:
        """
        Add instance to session with tenant validation.
        
        If instance has tenant_id and tenant context is set,
        ensure they match (unless explicitly bypassed).
        
        Args:
            instance: Model instance to add
            _warn: SQLAlchemy internal parameter
        """
        # If instance has tenant_id and tenant context is set, validate
        if hasattr(instance, 'tenant_id'):
            try:
                current_tenant_id = get_current_tenant_id()
                # If tenant_id is not set on instance, set it from context
                if instance.tenant_id is None:
                    instance.tenant_id = current_tenant_id
                # If tenant_id is set but doesn't match context, warn
                elif instance.tenant_id != current_tenant_id:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Instance tenant_id ({instance.tenant_id}) "
                        f"does not match context tenant_id ({current_tenant_id})"
                    )
            except TenantNotSetError:
                # No tenant context - allow but log
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(
                    f"Adding instance without tenant context: {type(instance).__name__}"
                )
        
        # Call parent add()
        super().add(instance, _warn=_warn)
