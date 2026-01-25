#!/usr/bin/env python3
"""
RISKCAST V3 - Server Startup Script
Script để khởi động server với error handling và validation
"""
import os
import sys
from pathlib import Path

# Đảm bảo thư mục gốc trong Python path
root_dir = Path(__file__).parent.resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Load .env file nếu có
try:
    from dotenv import load_dotenv
    env_file = root_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[INFO] Loaded .env from: {env_file}")
except ImportError:
    print("[WARNING] python-dotenv not installed, skipping .env loading")

def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    missing = []
    required = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'pydantic_settings'
    ]
    
    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"[ERROR] Missing dependencies: {', '.join(missing)}")
        print(f"[INFO] Install with: pip install {' '.join(missing)}")
        return False
    
    print("[OK] All required dependencies installed")
    return True

def check_database():
    """Kiểm tra database connection"""
    try:
        from app.database import init_db
        init_db()
        print("[OK] Database connection verified")
        return True
    except Exception as e:
        print(f"[WARNING] Database connection issue: {e}")
        print("[INFO] Server will start but database features may not work")
        print("[INFO] For SQLite, database will be created automatically on first use")
        return True  # Allow server to start anyway in dev mode

def start_server():
    """Khởi động server"""
    print("\n" + "="*60)
    print("RISKCAST V3 - Server Startup")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database (non-blocking)
    check_database()
    
    print("\n[INFO] Starting server on http://127.0.0.1:8000")
    print("[INFO] API Documentation: http://127.0.0.1:8000/docs")
    print("[INFO] Health Check: http://127.0.0.1:8000/health")
    print("[INFO] Press CTRL+C to stop the server\n")
    
    try:
        import uvicorn
        from app.config import settings
        
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,  # Enable auto-reload for development
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    start_server()
