@echo off
REM RISKCAST Server Startup Script
REM Run this file to start the server

echo ========================================
echo RISKCAST Server Startup
echo ========================================
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Set environment variables
set AUTH_ENABLED=true
set SESSION_SECRET=dev-secret-key-change-in-production-min-32-chars-here

echo Starting server...
echo Server will be available at: http://127.0.0.1:8000
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause
