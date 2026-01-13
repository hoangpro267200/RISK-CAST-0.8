# Start Vite Dev Server for React Results Page
# This script starts the Vite dev server on port 3000

Write-Host "🚀 Starting Vite Dev Server..." -ForegroundColor Cyan

# Change to project directory
$projectDir = "riskcast-v16-main"
if (Test-Path $projectDir) {
    Set-Location $projectDir
    Write-Host "✓ Changed to directory: $projectDir" -ForegroundColor Green
} else {
    Write-Host "❌ Directory not found: $projectDir" -ForegroundColor Red
    exit 1
}

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "⚠️  node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Check if backend is running on port 8000
Write-Host "🔍 Checking if backend is running on port 8000..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000" -Method GET -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Backend is running on port 8000" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Backend is not running on port 8000" -ForegroundColor Yellow
    Write-Host "   Please start backend server first using: .\start-server.ps1" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

# Start Vite dev server
Write-Host ""
Write-Host "🎯 Starting Vite dev server on http://localhost:3000" -ForegroundColor Cyan
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

npm run dev


