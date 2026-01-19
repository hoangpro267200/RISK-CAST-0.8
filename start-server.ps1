# RISKCAST Server Starter
# Chạy script này từ thư mục vcl để khởi động server

$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  RISKCAST Server Starter" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Xác định đường dẫn project
$projectDir = Join-Path $PSScriptRoot "riskcast-v16-main"

if (-not (Test-Path $projectDir)) {
    Write-Host "❌ ERROR: Project directory not found!" -ForegroundColor Red
    Write-Host "   Expected: $projectDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Project directory found" -ForegroundColor Green
Write-Host "  Location: $projectDir`n" -ForegroundColor Gray

# Kiểm tra port 8000 có đang được sử dụng không
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "⚠️  WARNING: Port 8000 is already in use!" -ForegroundColor Yellow
    Write-Host "   Process ID: $($portInUse.OwningProcess)" -ForegroundColor Gray
    $response = Read-Host "   Do you want to kill the existing process? (y/n)"
    if ($response -eq "y" -or $response -eq "Y") {
        Stop-Process -Id $portInUse.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "   ✓ Process killed" -ForegroundColor Green
        Start-Sleep -Seconds 1
    } else {
        Write-Host "   Exiting..." -ForegroundColor Yellow
        exit 1
    }
}

# Chuyển đến thư mục project
Push-Location $projectDir

try {
    Write-Host "🚀 Starting server...`n" -ForegroundColor Yellow
    Write-Host "   Server URL: http://127.0.0.1:8000" -ForegroundColor Cyan
    Write-Host "   API Docs: http://127.0.0.1:8000/docs`n" -ForegroundColor Cyan
    
    # Chạy server
    python dev_run.py
} catch {
    Write-Host "`n❌ ERROR: Failed to start server" -ForegroundColor Red
    Write-Host "   $($_.Exception.Message)" -ForegroundColor Yellow
    exit 1
} finally {
    Pop-Location
}
