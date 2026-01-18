#!/usr/bin/env python3
"""
RISKCAST - Development Server Runner
Run uvicorn with reload enabled for development
"""
import uvicorn
import multiprocessing
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    try:
        # Try to set UTF-8 encoding for Windows console
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, LookupError):
        # Fallback: use ASCII-safe output
        pass

# Load .env first
root_dir = Path(__file__).resolve().parent
env_file = root_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[INFO] Loaded .env from: {env_file}")
    
    # Verify API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and len(api_key) > 20 and api_key != "dummy":
        print("[INFO] ANTHROPIC_API_KEY configured")
    else:
        print("[WARNING] ANTHROPIC_API_KEY not found or invalid")

if __name__ == "__main__":
    try:
        # Windows multiprocessing fix
        multiprocessing.freeze_support()
        
        # Set PYTHONPATH và working directory
        os.environ["PYTHONPATH"] = str(root_dir)
        os.chdir(root_dir)
        sys.path.insert(0, str(root_dir))
        
        # Safe print function that handles encoding errors
        def safe_print(text):
            try:
                print(text)
            except UnicodeEncodeError:
                # Fallback: remove emojis and print ASCII-safe version
                safe_text = text.encode('ascii', 'ignore').decode('ascii')
                print(safe_text)
        
        safe_print("\n" + "="*60)
        safe_print("Starting RISKCAST Development Server")
        safe_print("="*60)
        safe_print(f"Server will run at: http://127.0.0.1:8000")
        safe_print(f"Working directory: {root_dir}")
        safe_print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
        safe_print(f"sys.path[0]: {sys.path[0]}")
        safe_print("="*60 + "\n")
        
        # Test import first
        try:
            from app.main import app
            safe_print("[INFO] App imported successfully")
        except Exception as e:
            print(f"[ERROR] Failed to import app: {e}")
            print(f"[DEBUG] Current directory: {os.getcwd()}")
            print(f"[DEBUG] Python path: {sys.path[:3]}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        # Run uvicorn with reload
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            workers=1,
            reload_dirs=["app"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


