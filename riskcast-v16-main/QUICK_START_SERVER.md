# Quick Start: Running the RISKCAST Server

## The Problem
If you see `ModuleNotFoundError: No module named 'app'`, you're running uvicorn from the wrong directory.

## Solution

### Option 1: Change Directory First (Recommended)
```powershell
# Navigate to project directory
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main

# Then run uvicorn
uvicorn app.main:app --reload
```

### Option 2: Use the run.py Script
```powershell
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
python run.py
```

### Option 3: Use PowerShell Script (if exists)
```powershell
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
.\start-server.ps1
```

## Important Notes

1. **Always run from `riskcast-v16-main` directory**
   - The `app` module is inside this directory
   - Python needs to find the `app` folder in the current directory

2. **Set Environment Variables** (if needed)
   ```powershell
   $env:AUTH_ENABLED = "true"
   $env:SESSION_SECRET = "your-secret-key-min-32-chars"
   ```

3. **Verify Server Started**
   - You should see: `INFO: Uvicorn running on http://127.0.0.1:8000`
   - Open browser to: `http://127.0.0.1:8000`

## Troubleshooting

### If still getting ModuleNotFoundError:
1. Check you're in the right directory:
   ```powershell
   Get-Location
   # Should show: C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
   ```

2. Verify `app` folder exists:
   ```powershell
   Test-Path app
   # Should return: True
   ```

3. List directory contents:
   ```powershell
   Get-ChildItem | Select-Object Name
   # Should show: app, src, requirements.txt, etc.
   ```
