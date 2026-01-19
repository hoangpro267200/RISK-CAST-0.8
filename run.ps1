# RISKCAST Quick Start Script
# Run this from the root directory to start the server

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RISKCAST Server - Quick Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$projectDir = Join-Path $PSScriptRoot "riskcast-v16-main"

if (-not (Test-Path $projectDir)) {
    Write-Host "ERROR: Project directory not found!" -ForegroundColor Red
    Write-Host "Expected: $projectDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Project directory found" -ForegroundColor Green
Write-Host "  Location: $projectDir`n" -ForegroundColor Gray

# Change to project directory
Push-Location $projectDir

try {
    Write-Host "Starting server...`n" -ForegroundColor Yellow
    python dev_run.py
} finally {
    Pop-Location
}








