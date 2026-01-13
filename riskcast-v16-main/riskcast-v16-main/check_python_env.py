#!/usr/bin/env python3
"""
Script kiểm tra Python environment và packages
"""
import sys
from pathlib import Path

print("=" * 70)
print("  KIỂM TRA PYTHON ENVIRONMENT")
print("=" * 70)
print()

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print()

# Check if packages are installed
packages_to_check = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "starlette",
    "jinja2"
]

print("Checking installed packages:")
print("-" * 70)
for package in packages_to_check:
    try:
        mod = __import__(package)
        version = getattr(mod, "__version__", "unknown")
        print(f"✓ {package:20s} - version: {version}")
    except ImportError:
        print(f"✗ {package:20s} - NOT INSTALLED")

print()
print("=" * 70)
print("  KẾT QUẢ")
print("=" * 70)
print()
print("Nếu tất cả packages đều có ✓, thì code sẽ chạy được.")
print("Cảnh báo trong VS Code chỉ là linter warnings, không ảnh hưởng runtime.")
print()








