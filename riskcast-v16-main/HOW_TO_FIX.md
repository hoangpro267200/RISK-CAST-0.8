# ✅ HOW TO FIX THE CONNECTION ERROR

## The Problem
You're getting `ERR_CONNECTION_REFUSED` because the server isn't running.

## Quick Fix (3 Steps)

### Step 1: Open PowerShell
Press `Win + X` and select "Windows PowerShell" or "Terminal"

### Step 2: Navigate to Project Directory
Copy and paste this command:
```powershell
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
```

### Step 3: Start the Server
Copy and paste this command:
```powershell
python -m uvicorn app.main:app --reload
```

**OR** double-click this file:
- `start-server-simple.bat`

## Expected Output
You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
INFO:     Application startup complete.
```

## Then Open Your Browser
Go to: **http://127.0.0.1:8000**

## If You See "ModuleNotFoundError"

**This means you're in the wrong directory!**

1. Check your current directory:
   ```powershell
   Get-Location
   ```

2. It should show:
   ```
   C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
   ```

3. If it shows something else, run:
   ```powershell
   cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
   ```

## Alternative: Use the Batch File

1. Navigate to the project folder in File Explorer:
   - `C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main`

2. Double-click: `start-server-simple.bat`

3. A window will open showing the server starting

4. Wait for: `INFO: Uvicorn running on http://127.0.0.1:8000`

5. Open your browser to: http://127.0.0.1:8000

## Still Not Working?

Check these:
- ✅ Python is installed: `python --version`
- ✅ You're in the right directory: `Get-Location`
- ✅ app folder exists: `Test-Path app`
- ✅ Port 8000 is not in use by another program

## Need Help?

The server must be running **before** you can access it in the browser!
Make sure you see the "Uvicorn running" message before opening the browser.
