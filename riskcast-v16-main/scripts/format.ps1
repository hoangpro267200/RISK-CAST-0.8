# RISKCAST Code Formatting Script (Windows PowerShell)
# Formats Python and TypeScript/JavaScript code

$ErrorActionPreference = "Continue"

Write-Host "Formatting RISKCAST Code" -ForegroundColor Green
Write-Host "================================"

# Python formatting (if black available)
try {
    $blackVersion = black --version 2>&1
    Write-Host "Formatting Python with black..." -ForegroundColor Yellow
    black app/ --line-length=120 --exclude='/(venv|\.venv|__pycache__)/'
} catch {
    Write-Host "black not installed, skipping Python format" -ForegroundColor Yellow
    Write-Host "Install with: pip install black"
}

# TypeScript/JavaScript formatting (if prettier available)
if (Get-Command npm -ErrorAction SilentlyContinue) {
    if (Test-Path "package.json") {
        if (Test-Path "node_modules") {
            try {
                npm list prettier 2>&1 | Out-Null
                Write-Host "Formatting TypeScript/JS with prettier..." -ForegroundColor Yellow
                npx prettier --write "src/**/*.{ts,tsx,js,jsx}"
            } catch {
                Write-Host "prettier not installed, skipping TypeScript/JS format" -ForegroundColor Yellow
                Write-Host "Install with: npm install --save-dev prettier"
            }
        } else {
            Write-Host "node_modules not found. Run 'npm install' first" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "npm not available, skipping TypeScript/JS format" -ForegroundColor Yellow
}

Write-Host "Formatting completed!" -ForegroundColor Green

