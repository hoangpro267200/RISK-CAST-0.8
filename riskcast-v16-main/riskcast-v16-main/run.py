#!/usr/bin/env python3
"""
RISKCAST - Production Server Runner
Run uvicorn in production mode (no reload)
"""
import uvicorn
import multiprocessing
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env first
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[INFO] Loaded .env from: {env_file}")

if __name__ == "__main__":
    try:
        # Windows multiprocessing fix
        multiprocessing.freeze_support()
        
        print("\n" + "="*60)
        print("🚀 Starting RISKCAST Production Server")
        print("="*60)
        print(f"📍 Server will run at: http://127.0.0.1:8000")
        print(f"📁 Working directory: {root_dir}")
        print("="*60 + "\n")
        
        # Test import first
        try:
            from app.main import app
            print("[INFO] App imported successfully ✓")
        except Exception as e:
            print(f"[ERROR] Failed to import app: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        # Run uvicorn in production mode
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            workers=1,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


