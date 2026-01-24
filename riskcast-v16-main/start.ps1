# RISKCAST Server - Quick Start
# Simple script to start the server

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RISKCAST Server - Quick Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "app\main.py")) {
    Write-Host "ERROR: Please run this script from the riskcast-v16-main directory" -ForegroundColor Red
    exit 1
}

# Check if migrations are needed
Write-Host "Checking database..." -ForegroundColor Yellow
try {
    python -c "from app.database import init_db; init_db()" 2>&1 | Out-Null
    Write-Host "✓ Database connection OK" -ForegroundColor Green
} catch {
    Write-Host "⚠ Database connection issue - make sure MySQL is running" -ForegroundColor Yellow
}

Write-Host "`nStarting server..." -ForegroundColor Yellow
Write-Host "Server will be available at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press CTRL+C to stop`n" -ForegroundColor Gray

# Start server
python dev_run.py
