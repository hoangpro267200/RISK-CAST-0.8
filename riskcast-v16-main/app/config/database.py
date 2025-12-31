"""
MySQL Database Configuration
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost:3306/riskcast?charset=utf8mb4"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable connection pooling for simplicity
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL logging
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False
    }
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database session
    
    Usage:
        with get_session() as db:
            db.add(...)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables
    """
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")


def drop_db():
    """
    Drop all database tables (USE WITH CAUTION)
    """
    from app.models import Base
    Base.metadata.drop_all(bind=engine)
    print("⚠ All database tables dropped")

