@echo off
echo ========================================
echo RISKCAST Server Starter
echo ========================================
echo.
cd /d "%~dp0"
echo Current directory: %CD%
echo.
echo Starting development server...
echo.
python dev_run.py
pause


