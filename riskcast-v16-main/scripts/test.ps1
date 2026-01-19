# RISKCAST Test Runner Script (Windows PowerShell)
# Run tests with proper configuration

$ErrorActionPreference = "Stop"

Write-Host "Running RISKCAST Tests" -ForegroundColor Green
Write-Host "================================"

# Check if pytest is installed
try {
    python -m pytest --version | Out-Null
} catch {
    Write-Host "Error: pytest is not installed" -ForegroundColor Red
    Write-Host "Install with: pip install pytest pytest-cov"
    exit 1
}

# Run tests
Write-Host "Running unit tests..." -ForegroundColor Yellow
python -m pytest tests/unit/ -v --tb=short

Write-Host "Running integration tests..." -ForegroundColor Yellow
python -m pytest tests/integration/ -v --tb=short

# Run with coverage if pytest-cov is installed
try {
    python -m pytest --collect-only -q 2>&1 | Select-String "pytest-cov" | Out-Null
    $hasCov = $true
} catch {
    $hasCov = $false
}

if ($hasCov) {
    Write-Host "Running with coverage..." -ForegroundColor Yellow
    python -m pytest tests/ --cov=app --cov-report=term --cov-report=html --tb=short
    Write-Host "Coverage report generated in htmlcov/index.html" -ForegroundColor Green
} else {
    Write-Host "pytest-cov not installed, skipping coverage" -ForegroundColor Yellow
    Write-Host "Install with: pip install pytest-cov"
}

Write-Host "Tests completed!" -ForegroundColor Green

