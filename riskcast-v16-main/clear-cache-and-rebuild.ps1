# Script để clear cache và rebuild frontend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CLEAR CACHE AND REBUILD" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Bước 1: Clear dist folder
Write-Host "[1/3] Clearing old build..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "  OK: dist folder cleared" -ForegroundColor Green
} else {
    Write-Host "  OK: dist folder does not exist" -ForegroundColor Green
}

# Bước 2: Rebuild frontend
Write-Host "[2/3] Rebuilding frontend..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK: Build successful" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Build failed" -ForegroundColor Red
    exit 1
}

# Bước 3: Instructions
Write-Host "[3/3] Instructions" -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. HARD REFRESH BROWSER (QUAN TRONG!):" -ForegroundColor Yellow
Write-Host "   - Press: Ctrl + Shift + R" -ForegroundColor White
Write-Host "   - Or: Ctrl + F5" -ForegroundColor White
Write-Host "   - Or: F12 -> Right-click Refresh -> 'Empty Cache and Hard Reload'" -ForegroundColor White
Write-Host ""
Write-Host "2. CLEAR BROWSER LOCALSTORAGE (if needed):" -ForegroundColor Yellow
Write-Host "   - Open DevTools (F12)" -ForegroundColor White
Write-Host "   - Go to Application tab -> Local Storage" -ForegroundColor White
Write-Host "   - Delete 'RISKCAST_RESULTS_V2' key" -ForegroundColor White
Write-Host "   - Or run in Console: localStorage.removeItem('RISKCAST_RESULTS_V2')" -ForegroundColor White
Write-Host ""
Write-Host "3. RESTART BACKEND SERVER:" -ForegroundColor Yellow
Write-Host "   - Stop current server (Ctrl+C)" -ForegroundColor White
Write-Host "   - Start again: python dev_run.py" -ForegroundColor White
Write-Host ""
Write-Host "4. TEST:" -ForegroundColor Yellow
Write-Host "   - Go to: http://127.0.0.1:8000/results" -ForegroundColor White
Write-Host "   - Check console for new logs" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
