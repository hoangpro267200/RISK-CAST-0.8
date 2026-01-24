# RISKCAST Server Startup Script
# This script ensures you're in the correct directory before starting the server

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RISKCAST Server Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get the script directory (project root)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow

# Verify app directory exists
if (-not (Test-Path "app")) {
    Write-Host "ERROR: 'app' directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the riskcast-v16-main directory" -ForegroundColor Red
    exit 1
}

Write-Host "✓ App directory found" -ForegroundColor Green

# Set environment variables if needed
if (-not $env:AUTH_ENABLED) {
    $env:AUTH_ENABLED = "true"
    Write-Host "✓ Set AUTH_ENABLED=true" -ForegroundColor Green
}

if (-not $env:SESSION_SECRET) {
    $env:SESSION_SECRET = "dev-secret-key-change-in-production-min-32-chars"
    Write-Host "✓ Set SESSION_SECRET (dev mode)" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host "Server will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
