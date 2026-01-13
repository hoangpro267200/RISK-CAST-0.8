# RISKCAST Linting Script (Windows PowerShell)
# Runs linting for both Python and TypeScript/JavaScript

$ErrorActionPreference = "Continue"

Write-Host "Running RISKCAST Linters" -ForegroundColor Green
Write-Host "================================"

# Python linting (if flake8/ruff available)
try {
    $flake8Version = flake8 --version 2>&1
    Write-Host "Running flake8..." -ForegroundColor Yellow
    flake8 app/ --max-line-length=120 --exclude=__pycache__,venv,.venv
} catch {
    try {
        $ruffVersion = ruff --version 2>&1
        Write-Host "Running ruff..." -ForegroundColor Yellow
        ruff check app/
    } catch {
        Write-Host "flake8/ruff not installed, skipping Python lint" -ForegroundColor Yellow
        Write-Host "Install with: pip install flake8 or pip install ruff"
    }
}

# TypeScript/JavaScript linting (if eslint available)
if (Get-Command npm -ErrorAction SilentlyContinue) {
    if (Test-Path "package.json") {
        if (Test-Path "node_modules") {
            Write-Host "Running ESLint..." -ForegroundColor Yellow
            npm run lint
        } else {
            Write-Host "node_modules not found. Run 'npm install' first" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "npm not available, skipping TypeScript/JS lint" -ForegroundColor Yellow
}

Write-Host "Linting completed!" -ForegroundColor Green

