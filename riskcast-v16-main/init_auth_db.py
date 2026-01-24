#!/usr/bin/env python3
"""
Initialize Auth Database Tables
Run this script to create all required auth tables.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.database import init_db
    print("=" * 60)
    print("Initializing Auth Database Tables...")
    print("=" * 60)
    init_db()
    print("=" * 60)
    print("SUCCESS: Database tables created!")
    print("=" * 60)
except Exception as e:
    print(f"ERROR: Failed to initialize database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
