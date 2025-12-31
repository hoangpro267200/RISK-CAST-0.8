# Install dependencies in venv
$projectDir = "riskcast-v16-main"
$venvPath = Join-Path $projectDir "venv"

Write-Host "`n=== Installing Dependencies ===" -ForegroundColor Cyan

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
}

# Activate venv
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $activateScript
} else {
    Write-Host "ERROR: Cannot find venv activation script!" -ForegroundColor Red
    exit 1
}

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
$requirementsFile = Join-Path $projectDir "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Host "`nInstalling packages from requirements.txt..." -ForegroundColor Yellow
    pip install -r $requirementsFile
} else {
    Write-Host "`nrequirements.txt not found, installing essential packages..." -ForegroundColor Yellow
    pip install fastapi uvicorn[standard] pydantic python-dotenv python-multipart jinja2 starlette
}

Write-Host "`n✓ Installation complete!" -ForegroundColor Green
Write-Host "`nYou can now run: .\start-server.ps1" -ForegroundColor Cyan








