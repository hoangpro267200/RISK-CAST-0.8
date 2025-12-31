#!/usr/bin/env python3
"""
Quick check script to verify Overview v33 is properly set up
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

files_to_check = [
    "app/templates/overview_v33.html",
    "app/static/css/overview_v33.css",
    "app/static/css/edit_panel.css",
    "app/static/css/ai_panel.css",
    "app/static/js/overview_v33.js",
    "app/static/js/edit_panel.js",
    "app/static/js/ai_panel.js",
    "app/routes/backend_overview_route_v33.py",
    "app/routes/update_shipment_route_v33.py",
    "app/routes/ai_endpoints_v33.py",
]

print("🔍 Checking Overview v33 Files...\n")

all_exist = True
for file_path in files_to_check:
    full_path = BASE_DIR / file_path
    exists = full_path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {file_path}")
    if not exists:
        all_exist = False

print("\n" + "="*50)

# Check route
route_file = BASE_DIR / "app/routes/overview.py"
if route_file.exists():
    content = route_file.read_text(encoding='utf-8')
    if 'overview_v33.html' in content:
        print("✅ Route overview.py uses overview_v33.html")
    else:
        print("❌ Route overview.py does NOT use overview_v33.html")
        print("   Should contain: overview_v33.html")
        all_exist = False
else:
    print("❌ Route file not found: app/routes/overview.py")
    all_exist = False

# Check main.py
main_file = BASE_DIR / "app/main.py"
if main_file.exists():
    content = main_file.read_text(encoding='utf-8')
    if 'update_shipment_router' in content and 'ai_endpoints_router' in content:
        print("✅ main.py includes v33 routes")
    else:
        print("⚠️  main.py may not include all v33 routes")
        print("   Should include: update_shipment_router, ai_endpoints_router")

print("\n" + "="*50)

if all_exist:
    print("\n✅ All v33 files exist!")
    print("\n📝 Next steps:")
    print("   1. Restart server: uvicorn app.main:app --reload")
    print("   2. Clear browser cache: Ctrl+Shift+R")
    print("   3. Open: http://127.0.0.1:8000/overview")
    print("   4. Check console for: '[Overview v33] Initializing...'")
else:
    print("\n❌ Some files are missing!")
    print("   Please check the file paths above.")

