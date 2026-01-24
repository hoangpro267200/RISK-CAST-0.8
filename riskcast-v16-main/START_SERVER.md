# 🚀 How to Start the Server

## Problem
If you get `ModuleNotFoundError: No module named 'app'`, you're running uvicorn from the wrong directory.

## Solution

### Step 1: Navigate to the project directory
```powershell
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
```

### Step 2: Start the server
```powershell
uvicorn app.main:app --reload
```

## Alternative: Run from parent directory
If you're in `C:\Users\RIM\OneDrive\Desktop\ok\`, use:
```powershell
cd riskcast-v16-main
uvicorn app.main:app --reload
```

## Verify it's working
After starting, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Then visit: http://127.0.0.1:8000/

## Quick Start Script (Optional)
Create a file `start.ps1` in the project root:
```powershell
# start.ps1
cd $PSScriptRoot
uvicorn app.main:app --reload
```

Then run: `.\start.ps1`
