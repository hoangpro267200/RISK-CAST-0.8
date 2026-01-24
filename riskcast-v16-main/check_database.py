#!/usr/bin/env python3
"""Check database tables for auth system"""
import sys
sys.path.insert(0, '.')

from app.database import engine, Base
from sqlalchemy import inspect
from app.models.auth import User, Session, PasswordResetToken

print("=== PHASE 1: DATABASE VERIFICATION ===")
print()

# Check existing tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Existing tables: {tables}")
print()

required = ['users', 'sessions', 'password_reset_tokens']
missing = [t for t in required if t not in tables]

print(f"Required tables: {required}")
print()

if missing:
    print(f"FAIL: MISSING TABLES: {missing}")
    print("Creating tables...")
    Base.metadata.create_all(engine)
    print("PASS: Tables created")
    print()
    
    # Refresh inspector
    inspector = inspect(engine)
    tables_after = inspector.get_table_names()
    created = [t for t in required if t in tables_after]
    print(f"Tables after creation: {created}")
    if len(created) == len(required):
        print("PASS: All required tables exist")
    else:
        print(f"FAIL: Missing {set(required) - set(created)}")
else:
    print("PASS: All required tables exist")
    print()

# Show table schemas (refresh inspector)
inspector = inspect(engine)
print("Table schemas:")
for table in required:
    if table in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns(table)]
        print(f"  {table}: {cols}")
    else:
        print(f"  {table}: NOT FOUND")
