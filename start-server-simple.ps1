# RISKCAST Server Starter (Simple - Direct uvicorn)
# This script starts uvicorn directly from the correct directory

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Join-Path $scriptDir "riskcast-v16-main"

if (-not (Test-Path $projectDir)) {
    Write-Host "ERROR: Project directory not found: $projectDir" -ForegroundColor Red
    exit 1
}

Set-Location $projectDir
uvicorn app.main:app --reload










