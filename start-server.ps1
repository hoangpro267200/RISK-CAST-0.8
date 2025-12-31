# ========================================
# RISKCAST SERVER - START SCRIPT
# ========================================
# Chạy script này từ thư mục gốc để khởi động server

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RISKCAST Server Starter" -ForegroundColor Cyan  
Write-Host "========================================`n" -ForegroundColor Cyan

# Kiểm tra và dừng process cũ nếu có
Write-Host "Checking for running processes..." -ForegroundColor Yellow
$oldProcess = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*dev_run*" }
if ($oldProcess) {
    Write-Host "Found running server process. Stopping..." -ForegroundColor Yellow
    Stop-Process -Name python -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Đường dẫn đến project
$projectDir = Join-Path $PSScriptRoot "riskcast-v16-main"

if (-not (Test-Path $projectDir)) {
    Write-Host "`n❌ ERROR: Không tìm thấy thư mục project!" -ForegroundColor Red
    Write-Host "   Expected: $projectDir" -ForegroundColor Yellow
    Write-Host "`nHãy đảm bảo bạn đang chạy script từ thư mục gốc." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "✓ Project directory found" -ForegroundColor Green
Write-Host "  Location: $projectDir`n" -ForegroundColor Gray

# Chuyển đến thư mục project
Push-Location $projectDir

# Kiểm tra và activate venv nếu có
$venvPath = Join-Path $projectDir "venv"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "✓ Virtual environment found" -ForegroundColor Green
    Write-Host "  Activating venv...`n" -ForegroundColor Gray
    & $venvActivate
} else {
    Write-Host "⚠ No virtual environment found, using system Python`n" -ForegroundColor Yellow
}

# Set PYTHONPATH để đảm bảo Python tìm thấy module app
$env:PYTHONPATH = $projectDir
Write-Host "✓ PYTHONPATH set to: $projectDir`n" -ForegroundColor Green

try {
    Write-Host "Starting RISKCAST server..." -ForegroundColor Yellow
    Write-Host "Server will be available at: http://127.0.0.1:8000`n" -ForegroundColor Green
    Write-Host "Press CTRL+C to stop the server`n" -ForegroundColor Gray
    Write-Host ("=" * 50) -ForegroundColor Cyan
    Write-Host ""
    
    # Chạy server với Python từ venv hoặc system
    if (Test-Path $venvActivate) {
        & "$venvPath\Scripts\python.exe" dev_run.py
    } else {
        python dev_run.py
    }
} catch {
    Write-Host "`n❌ ERROR: Không thể khởi động server!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
} finally {
    Pop-Location
    Write-Host "`nServer stopped." -ForegroundColor Gray
}
