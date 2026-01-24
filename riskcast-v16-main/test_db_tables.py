#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Phase 1 database verification"""

import sys
import io

# Set stdout to UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=== Database Table Check ===")

try:
    from app.database import engine, Base
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Existing tables: {tables}")
    
    required = ['users', 'sessions', 'password_reset_tokens']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"[WARN] MISSING TABLES: {missing}")
        print("Creating tables...")
        from app.models.auth import User, Session, PasswordResetToken
        Base.metadata.create_all(engine)
        print("[PASS] Tables created")
        
        # Verify
        tables_after = inspect(engine).get_table_names()
        print(f"Tables after creation: {tables_after}")
        
        # Check again
        missing_after = [t for t in required if t not in tables_after]
        if missing_after:
            print(f"[FAIL] Still missing: {missing_after}")
        else:
            print("[PASS] All required tables exist")
    else:
        print("[PASS] All required tables exist")
    
    # Show table schema
    print("\n=== Table Schemas ===")
    for table in required:
        if table in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns(table)]
            print(f"{table}: {cols}")
        else:
            print(f"{table}: NOT FOUND")
            
except Exception as e:
    print(f"[FAIL] Database check FAILED: {e}")
    import traceback
    traceback.print_exc()
