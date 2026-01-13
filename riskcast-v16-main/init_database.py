"""
Initialize MySQL Database - Create all tables
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config.database import init_db

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 RISKCAST: Initialize MySQL Database")
    print("=" * 60)
    print()
    
    try:
        init_db()
        print()
        print("✅ Database initialized successfully!")
        print()
        print("Next steps:")
        print("1. Set USE_MYSQL=true in .env file")
        print("2. Run migration: python app/migrations/migrate_to_mysql.py")
        print("3. Restart backend server")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print()
        print("Please check:")
        print("1. MySQL server is running")
        print("2. DATABASE_URL in .env is correct")
        print("3. Database 'riskcast' exists")
        sys.exit(1)


