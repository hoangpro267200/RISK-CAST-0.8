"""
Database configuration and connection management.

RISKCAST v17 - Database Layer
"""

from sqlalchemy import create_engine
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
    Initialize database - create all tables.
    
    Call this on application startup:
        from app.database import init_db
        init_db()
    """
    # Import all models so they're registered with Base
    from app.models import api_key, audit_trail, conversation
    
    Base.metadata.create_all(bind=engine)
    print("[Database] ✅ Tables created successfully")


def drop_db():
    """Drop all tables - USE WITH CAUTION."""
    Base.metadata.drop_all(bind=engine)
    print("[Database] ⚠️ All tables dropped")


# Export common items
__all__ = ['Base', 'engine', 'SessionLocal', 'get_db', 'init_db']
