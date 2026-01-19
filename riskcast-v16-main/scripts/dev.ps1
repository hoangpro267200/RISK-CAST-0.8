# RISKCAST Development Server Script (Windows PowerShell)
# Starts both backend and frontend dev servers

$ErrorActionPreference = "Stop"

Write-Host "Starting RISKCAST Development Environment" -ForegroundColor Green
Write-Host "=========================================="

# Check if virtual environment exists
if (-not (Test-Path "venv") -and -not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

# Install Python dependencies if needed
$installedFlag = "venv\.installed"
if (-not (Test-Path $installedFlag)) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if (Test-Path "requirements-dev.txt") {
        pip install -r requirements-dev.txt
    }
    New-Item -ItemType File -Path $installedFlag -Force | Out-Null
    Write-Host "Python dependencies installed" -ForegroundColor Green
}

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    $NODE_AVAILABLE = $true
} catch {
    Write-Host "Node.js not found. Frontend dev server will not start." -ForegroundColor Yellow
    Write-Host "Install Node.js from: https://nodejs.org/"
    $NODE_AVAILABLE = $false
}

# Install npm dependencies if needed
if ($NODE_AVAILABLE -and -not (Test-Path "node_modules")) {
    Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
    npm install
    Write-Host "npm dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting servers..." -ForegroundColor Blue
Write-Host ""

# Start backend server
Write-Host "Backend: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "API Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python dev_run.py
}

# Start frontend dev server if Node.js available
if ($NODE_AVAILABLE) {
    Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        npm run dev
    }
}

Write-Host ""
Write-Host "Development servers started!" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow
Write-Host ""

# Wait for user interrupt
try {
    Wait-Job $backendJob, $frontendJob | Out-Null
} finally {
    Write-Host ""
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    if ($NODE_AVAILABLE) {
        Stop-Job $frontendJob -ErrorAction SilentlyContinue
        Remove-Job $frontendJob -ErrorAction SilentlyContinue
    }
}

