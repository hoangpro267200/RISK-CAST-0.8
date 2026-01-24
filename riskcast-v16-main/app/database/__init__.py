"""
Database configuration and connection management.

RISKCAST v17 - Database Layer
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Base class for SQLAlchemy models
Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///./riskcast.db'  # Default to SQLite for development
)

# Convert postgres:// to postgresql:// (for Heroku compatibility)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create engine with appropriate settings
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite needs this
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800  # Recycle connections after 30 minutes
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Usage with FastAPI:
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
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
        print("[Database] Connection verified")
        print("[Database] Note: Run 'alembic upgrade head' to create/update tables")
    except Exception as e:
        print(f"[Database] Connection error: {e}")
        print("[Database] Make sure database exists and migrations are run: alembic upgrade head")
        # Don't raise in development - allow server to start
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            raise


def drop_db():
    """Drop all tables - USE WITH CAUTION."""
    Base.metadata.drop_all(bind=engine)
    print("[Database] ⚠️ All tables dropped")


# Export common items
__all__ = ['Base', 'engine', 'SessionLocal', 'get_db', 'init_db']

# Try to import V3 additions (TenantScopedSession) from parent database.py module
# Note: This allows importing from both app.database (package) and app.database (module)
try:
    # Import from the parent database.py file
    import importlib
    import pathlib
    
    # Get parent directory
    parent_dir = pathlib.Path(__file__).parent.parent
    db_module_path = parent_dir / 'database.py'
    
    if db_module_path.exists():
        # Load the module
        loader = importlib.machinery.SourceFileLoader('app_database_v3', str(db_module_path))
        db_v3 = loader.load_module()
        
        # Export TenantScopedSession and get_tenant_scoped_db if available
        if hasattr(db_v3, 'TenantScopedSession'):
            TenantScopedSession = db_v3.TenantScopedSession
            __all__.append('TenantScopedSession')
        
        if hasattr(db_v3, 'get_tenant_scoped_db'):
            get_tenant_scoped_db = db_v3.get_tenant_scoped_db
            __all__.append('get_tenant_scoped_db')
except Exception as e:
    # If import fails, TenantScopedSession won't be available from app.database package
    # Users can import directly: from app.database import TenantScopedSession
    # (Python will import from app/database.py instead of app/database/__init__.py)
    pass
