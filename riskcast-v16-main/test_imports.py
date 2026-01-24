#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Phase 0 import verification"""

import sys
import io

# Set stdout to UTF-8 for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=== Backend Imports ===")

try:
    from app.main import app
    print("[PASS] app.main imports OK")
except Exception as e:
    print(f"[FAIL] app.main FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.models.auth import User, Session, PasswordResetToken
    print("[PASS] auth models import OK")
except Exception as e:
    print(f"[FAIL] auth models FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.routers.auth import router as auth_router
    print("[PASS] auth router imports OK")
except Exception as e:
    print(f"[FAIL] auth router FAILED: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.dependencies.auth import get_current_user, require_auth
    print("[PASS] auth dependencies import OK")
except Exception as e:
    print(f"[FAIL] auth dependencies FAILED: {e}")
    import traceback
    traceback.print_exc()
