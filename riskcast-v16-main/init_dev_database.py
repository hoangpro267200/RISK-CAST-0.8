#!/usr/bin/env python3
"""
Initialize Development Database (SQLite)

Creates all tables required for development mode.
For production, use Alembic migrations with PostgreSQL.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment for development
os.environ.setdefault("ENVIRONMENT", "development")

def main():
    print("=" * 60)
    print("RISKCAST: Initialize Development Database (SQLite)")
    print("=" * 60)
    print()
    
    try:
        # Load environment
        from dotenv import load_dotenv
        load_dotenv(project_root / ".env")
        
        # Import database components
        from app.database import Base, engine
        from app.config import settings
        
        print(f"Environment: {settings.ENVIRONMENT}")
        print(f"Database URL: {settings.DATABASE_URL}")
        print()
        
        # Import core models to ensure they're registered with Base.metadata
        print("Loading models...")
        models_loaded = []
        
        # Core models
        try:
            from app.models.shipment import ShipmentDB
            from app.models.risk_analysis import RiskAnalysis
            from app.models.scenario import Scenario
            from app.models.kv_store import KVStore
            models_loaded.append("Core models")
        except Exception as e:
            print(f"  - Warning: Core models: {e}")
        
        # Auth models (uses separate AuthBase to avoid ORM conflicts)
        try:
            from app.models.auth import AuthUser, Session, PasswordResetToken, AuthBase
            from app.models.account import AuditLog, UserPreference, OAuthIdentity, EventLog
            models_loaded.append("Auth models")
        except Exception as e:
            print(f"  - Warning: Auth models: {e}")
        
        # Tenancy models (V3)
        try:
            from app.modules.tenancy.models import Tenant, Membership
            models_loaded.append("Tenancy models")
        except Exception as e:
            print(f"  - Warning: Tenancy models: {e}")
        
        # Risk assessment models
        try:
            from app.modules.risk_assessments.models import RiskAssessment
            models_loaded.append("Risk assessment models")
        except Exception as e:
            print(f"  - Warning: Risk assessment models: {e}")
        
        # Risk run models
        try:
            from app.modules.risk_runs.models import RiskRun
            models_loaded.append("Risk run models")
        except Exception as e:
            print(f"  - Warning: Risk run models: {e}")
        
        # Model versioning
        try:
            from app.modules.model_versioning.models import ModelVersion
            models_loaded.append("Model versioning")
        except Exception as e:
            print(f"  - Warning: Model versioning: {e}")
        
        for m in models_loaded:
            print(f"  - {m} loaded")
        
        print()
        print("Creating tables...")
        
        # Create main tables
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        # Create auth tables (separate AuthBase)
        try:
            from app.models.auth import AuthBase
            AuthBase.metadata.create_all(bind=engine, checkfirst=True)
            print("  - Auth tables created")
        except Exception as e:
            print(f"  - Warning: Auth tables: {e}")
        
        print()
        print("=" * 60)
        print("Database initialized successfully!")
        print("=" * 60)
        print()
        print(f"Tables registered ({len(Base.metadata.tables)}):")
        for table_name in sorted(Base.metadata.tables.keys()):
            print(f"  - {table_name}")
        print()
        print("Next steps:")
        print("1. Start the server: python start_server.py")
        print("2. Access docs at: http://127.0.0.1:8000/docs")
        print("3. Health check: http://127.0.0.1:8000/health")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
