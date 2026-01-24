"""
Database Configuration and Session Management
RISKCAST V3 - Modular Monolith
MySQL with SQLAlchemy 2.0+
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, Query
from sqlalchemy.pool import QueuePool
from typing import Generator, Optional, Any, List
from fastapi import Depends, Request
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create engine with MySQL connection pooling
# Database URL format: mysql+pymysql://user:password@localhost:3306/riskcast_v3
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using (important for MySQL)
    pool_recycle=3600,   # Recycle connections after 1 hour
    # MySQL-specific settings
    connect_args={
        "charset": "utf8mb4",
        "use_unicode": True,
    } if "mysql" in settings.DATABASE_URL.lower() else {},
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database connection.
    
    Note: Tables should be created via Alembic migrations, not here.
    Run: alembic upgrade head
    
    This function only verifies database connectivity.
    """
    try:
        # Just verify connection - don't create tables
        # Tables should be created via: alembic upgrade head
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
        logger.info("Note: Run 'alembic upgrade head' to create/update tables")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        logger.warning("Make sure database exists and migrations are run: alembic upgrade head")
        # Don't raise in development - allow server to start
        if settings.ENVIRONMENT == "production":
            raise


@event.listens_for(engine, "connect")
def set_mysql_settings(dbapi_conn, connection_record):
    """Set MySQL-specific settings on connection"""
    if "mysql" in settings.DATABASE_URL.lower():
        cursor = dbapi_conn.cursor()
        # Set timezone to UTC
        cursor.execute("SET time_zone = '+00:00'")
        # Enable foreign keys (InnoDB default, but explicit is better)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        # Set charset
        cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.close()
        logger.debug("MySQL connection settings applied")


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas if using SQLite (for development/testing)"""
    if "sqlite" in settings.DATABASE_URL.lower():
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        logger.debug("SQLite pragmas applied")


class TenantScopedSession:
    """
    Database session wrapper that enforces tenant scoping.
    
    All queries on tenant-scoped models must include tenant_id filter.
    This prevents data leakage between tenants by automatically applying
    tenant_id filters to all queries.
    
    Features:
    - Automatic tenant_id filtering on queries
    - Automatic tenant_id assignment on add()
    - Validation that tenant_id matches session tenant
    - Proxy methods for all common session operations
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            context: TenantContext = Depends(resolve_tenant_context),
            db: TenantScopedSession = Depends(get_tenant_scoped_db)
        ):
            # All queries automatically filtered by tenant_id
            assessments = db.query(RiskAssessment).all()
    """
    
    def __init__(self, session: Session, tenant_id: str):
        """
        Initialize tenant-scoped session.
        
        Args:
            session: Underlying SQLAlchemy session
            tenant_id: Tenant ID to scope all queries to
        """
        self._session = session
        self._tenant_id = tenant_id
        logger.debug(f"TenantScopedSession created for tenant_id={tenant_id}")
    
    @property
    def tenant_id(self) -> str:
        """Get the tenant ID for this session"""
        return self._tenant_id
    
    def query(self, *entities, **kwargs):
        """
        Create query with automatic tenant scoping for tenant-scoped models.
        
        For models with __tenant_scoped__ = True, automatically adds
        tenant_id filter to prevent cross-tenant data access.
        
        Args:
            *entities: Model classes to query
            **kwargs: Additional query arguments
            
        Returns:
            Query object with tenant_id filter applied
        """
        q = self._session.query(*entities, **kwargs)
        
        # Apply tenant filter for each tenant-scoped entity
        for entity in entities:
            # Check if entity is a class with __tenant_scoped__ marker
            if hasattr(entity, '__tenant_scoped__') and entity.__tenant_scoped__:
                # Check if tenant_id column exists
                if hasattr(entity, 'tenant_id'):
                    q = q.filter(entity.tenant_id == self._tenant_id)
                    logger.debug(
                        f"Applied tenant filter for {entity.__name__}: tenant_id={self._tenant_id}"
                    )
        
        return q
    
    def add(self, instance):
        """
        Add instance to session with automatic tenant_id assignment.
        
        For tenant-scoped models:
        - If tenant_id is None, sets it to session tenant_id
        - If tenant_id is set, validates it matches session tenant_id
        - Raises ValueError if tenant_id doesn't match
        
        Args:
            instance: Model instance to add
            
        Returns:
            Result of underlying session.add()
            
        Raises:
            ValueError: If instance has different tenant_id
        """
        # Check if instance is tenant-scoped
        if hasattr(instance, '__tenant_scoped__') and instance.__tenant_scoped__:
            if hasattr(instance, 'tenant_id'):
                if instance.tenant_id is None:
                    # Auto-assign tenant_id
                    instance.tenant_id = self._tenant_id
                    logger.debug(
                        f"Auto-assigned tenant_id={self._tenant_id} to {instance.__class__.__name__}"
                    )
                elif instance.tenant_id != self._tenant_id:
                    # Tenant mismatch - security violation
                    raise ValueError(
                        f"Cannot add {instance.__class__.__name__} with tenant_id={instance.tenant_id} "
                        f"to session scoped to tenant_id={self._tenant_id}"
                    )
        
        return self._session.add(instance)
    
    def add_all(self, instances: List[Any]):
        """Add multiple instances with tenant validation"""
        for instance in instances:
            self.add(instance)
        return self._session
    
    def delete(self, instance):
        """Delete instance (with tenant validation)"""
        # Validate tenant_id matches for tenant-scoped models
        if hasattr(instance, '__tenant_scoped__') and instance.__tenant_scoped__:
            if hasattr(instance, 'tenant_id'):
                if instance.tenant_id != self._tenant_id:
                    raise ValueError(
                        f"Cannot delete {instance.__class__.__name__} with tenant_id={instance.tenant_id} "
                        f"from session scoped to tenant_id={self._tenant_id}"
                    )
        return self._session.delete(instance)
    
    def commit(self):
        """Commit transaction"""
        return self._session.commit()
    
    def rollback(self):
        """Rollback transaction"""
        return self._session.rollback()
    
    def flush(self):
        """Flush pending changes"""
        return self._session.flush()
    
    def refresh(self, instance, attribute_names=None):
        """Refresh instance from database"""
        return self._session.refresh(instance, attribute_names)
    
    def expire(self, instance, attribute_names=None):
        """Expire instance attributes"""
        return self._session.expire(instance, attribute_names)
    
    def merge(self, instance):
        """Merge instance into session"""
        # Validate tenant_id for tenant-scoped models
        if hasattr(instance, '__tenant_scoped__') and instance.__tenant_scoped__:
            if hasattr(instance, 'tenant_id') and instance.tenant_id:
                if instance.tenant_id != self._tenant_id:
                    raise ValueError(
                        f"Cannot merge {instance.__class__.__name__} with tenant_id={instance.tenant_id} "
                        f"into session scoped to tenant_id={self._tenant_id}"
                    )
        return self._session.merge(instance)
    
    def get(self, entity, ident):
        """
        Get instance by primary key.
        
        WARNING: This method does NOT automatically filter by tenant_id.
        Use query() instead for tenant-scoped models to ensure safety.
        
        Args:
            entity: Model class
            ident: Primary key value
            
        Returns:
            Instance or None (if tenant_id doesn't match)
        """
        instance = self._session.get(entity, ident)
        
        # Validate tenant_id for tenant-scoped models
        if instance and hasattr(instance, '__tenant_scoped__') and instance.__tenant_scoped__:
            if hasattr(instance, 'tenant_id'):
                if instance.tenant_id != self._tenant_id:
                    logger.warning(
                        f"get() returned {instance.__class__.__name__} with tenant_id={instance.tenant_id} "
                        f"for session scoped to tenant_id={self._tenant_id}. Returning None."
                    )
                    return None
        
        return instance
    
    def execute(self, statement, params=None, execution_options=None):
        """Execute statement (use with caution - no automatic tenant filtering)"""
        logger.warning(
            "execute() called on TenantScopedSession - tenant filtering not guaranteed. "
            "Consider using query() instead."
        )
        return self._session.execute(statement, params, execution_options)
    
    def close(self):
        """Close session"""
        return self._session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()
    
    # Expose underlying session for advanced use cases (use with caution)
    @property
    def _raw_session(self) -> Session:
        """
        Get underlying raw session.
        
        WARNING: Using this bypasses tenant scoping. Only use for:
        - Queries on non-tenant-scoped models (e.g., Tenant, User)
        - Administrative operations
        - Operations that explicitly handle tenant_id
        
        Returns:
            Underlying SQLAlchemy session
        """
        logger.warning("Accessing raw session - tenant scoping bypassed")
        return self._session


# SQLAlchemy event listener for additional safety
@event.listens_for(Query, "before_compile", retval=True)
def enforce_tenant_scope(query: Query):
    """
    Event listener that warns if tenant-scoped model queried without tenant_id filter.
    
    This is a safety net - primary enforcement should be in TenantScopedSession.
    This listener checks queries and logs warnings if tenant-scoped models are
    queried without explicit tenant_id filters.
    
    Note: This is a best-effort check and may not catch all cases. Always use
    TenantScopedSession for tenant-scoped models.
    """
    # Get the entities being queried
    entities = query.column_descriptions
    
    for entity_desc in entities:
        entity = entity_desc.get('entity')
        if entity is None:
            continue
        
        # Check if entity is tenant-scoped
        if hasattr(entity, '__tenant_scoped__') and entity.__tenant_scoped__:
            # Log debug message (not warning, as TenantScopedSession handles this)
            logger.debug(
                f"Query on tenant-scoped model {entity.__name__} - "
                f"ensure tenant_id filter is present (TenantScopedSession handles this)"
            )
    
    return query


async def get_tenant_scoped_db(
    request: Request,
    db: Session = Depends(get_db)
) -> TenantScopedSession:
    """
    FastAPI dependency for tenant-scoped database session.
    
    This dependency automatically gets TenantContext from request.state,
    which is set by resolve_tenant_context dependency.
    
    IMPORTANT: This dependency requires resolve_tenant_context to be called first.
    FastAPI will automatically resolve dependencies in order.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            context: TenantContext = Depends(resolve_tenant_context),
            db: TenantScopedSession = Depends(get_tenant_scoped_db)
        ):
            # All queries automatically filtered by tenant_id
            assessments = db.query(RiskAssessment).all()
    
    Alternative usage (recommended):
        from app.shared.dependencies import require_tenant
        
        @router.get("/endpoint")
        async def endpoint(
            context: TenantContext = Depends(require_tenant()),
            db: TenantScopedSession = Depends(get_tenant_scoped_db)
        ):
            assessments = db.query(RiskAssessment).all()
    
    Args:
        request: FastAPI request object (injected automatically)
        db: Raw database session (injected by FastAPI)
        
    Returns:
        TenantScopedSession scoped to the tenant
        
    Raises:
        ValueError: If TenantContext is not found in request.state
    """
    # Import here to avoid circular dependency
    from fastapi import Request
    from app.shared.dependencies import TenantContext
    
    # Get context from request state (set by resolve_tenant_context)
    if request is None:
        # Try to get from current request context
        # This is a fallback - ideally request should be injected
        raise ValueError(
            "Request object required. Ensure resolve_tenant_context is called first. "
            "FastAPI should inject Request automatically."
        )
    
    context = getattr(request.state, "tenant_context", None)
    
    if context is None:
        raise ValueError(
            "TenantContext not found in request.state. "
            "Ensure resolve_tenant_context is called before get_tenant_scoped_db. "
            "Example: context: TenantContext = Depends(resolve_tenant_context)"
        )
    
    if not isinstance(context, TenantContext):
        raise ValueError(
            f"Expected TenantContext in request.state, got {type(context)}"
        )
    
    if not context.tenant_id:
        raise ValueError("TenantContext.tenant_id is required")
    
    return TenantScopedSession(db, context.tenant_id)
