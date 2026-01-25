#!/usr/bin/env python3
"""
Setup Auth Database Tables
Creates all required tables for authentication system.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_auth_db():
    """Create all auth-related tables."""
    print("=" * 60)
    print("Setting up Auth Database Tables...")
    print("=" * 60)
    
    try:
        from app.database import engine, Base
        
        # Import all models to register them with Base
        from app.models.auth import AuthUser, Session, PasswordResetToken
        from app.models.account import AuditLog, UserPreference, OAuthIdentity, EventLog
        
        print(f"Database URL: {engine.url}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("Tables created:")
        for table in Base.metadata.tables:
            print(f"  - {table}")
        
        print("=" * 60)
        print("SUCCESS: Auth database tables created!")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. Restart the backend server")
        print("  2. Access /login or /signup to test auth")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    setup_auth_db()
