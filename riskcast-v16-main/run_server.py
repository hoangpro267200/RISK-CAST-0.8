#!/usr/bin/env python3
"""
RISKCAST Server Runner
Run uvicorn with proper Windows multiprocessing support
"""
import uvicorn
import sys
import os
from pathlib import Path

# Load .env first
from dotenv import load_dotenv
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[INFO] Loaded .env from: {env_file}")
    
    # Verify API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and len(api_key) > 20:
        print("[INFO] ANTHROPIC_API_KEY configured ✓")
    else:
        print("[WARNING] ANTHROPIC_API_KEY not found or invalid")

if __name__ == "__main__":
    # Fix Windows multiprocessing
    if sys.platform == "win32":
        import multiprocessing
        multiprocessing.freeze_support()
    
    # Run uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )


