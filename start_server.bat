@echo off
REM RISKCAST V3 - Windows Startup Script (Wrapper)
echo ========================================
echo RISKCAST V3 - Server Startup
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Run the Python startup script (wrapper sẽ tự động cd vào riskcast-v16-main)
echo [INFO] Starting server...
python start_server.py

pause
