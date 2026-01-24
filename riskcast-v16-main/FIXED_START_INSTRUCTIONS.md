# ✅ Server Fix - Quick Start Instructions

## The Problem Was Fixed!
The issue was running `uvicorn` from the wrong directory.

## ✅ Server Should Now Be Running

The server has been started in the background. Check your browser at:
**http://127.0.0.1:8000**

## If Server Still Doesn't Work

### Method 1: Manual Start (Recommended)
Open PowerShell and run:

```powershell
# Navigate to project directory
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main

# Start server
uvicorn app.main:app --reload
```

### Method 2: Use Python Script
```powershell
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
python run.py
```

### Method 3: Use PowerShell Script
```powershell
cd C:\Users\RIM\OneDrive\Desktop\ok\riskcast-v16-main
.\START_SERVER_FIXED.ps1
```

## Verify Server is Running

1. **Check Terminal Output:**
   - Should see: `INFO: Uvicorn running on http://127.0.0.1:8000`
   - Should see: `INFO: Application startup complete.`

2. **Check Browser:**
   - Open: http://127.0.0.1:8000
   - Should see the RISKCAST home page

3. **Check Health Endpoint:**
   ```powershell
   curl http://127.0.0.1:8000/health
   ```

## Important Notes

✅ **Always run from `riskcast-v16-main` directory**  
✅ **The `app` module must be in the current directory**  
✅ **Environment variables are automatically set by the script**

## Troubleshooting

If you still see `ModuleNotFoundError`:
1. Verify you're in the right directory:
   ```powershell
   Get-Location
   # Should show: ...\ok\riskcast-v16-main
   ```

2. Check app folder exists:
   ```powershell
   Test-Path app
   # Should return: True
   ```

3. List files:
   ```powershell
   Get-ChildItem | Select-Object Name
   # Should see: app, src, requirements.txt
   ```
