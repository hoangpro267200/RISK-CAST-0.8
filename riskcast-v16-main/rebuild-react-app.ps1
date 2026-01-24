# Rebuild React App Script
# Script to rebuild React app and fix 404 errors

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Rebuilding React App" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Step 1: Clean dist folder
Write-Host ""
Write-Host "[1/3] Cleaning dist folder..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item -Recurse -Force dist
    Write-Host "[OK] Cleaned dist folder" -ForegroundColor Green
} else {
    Write-Host "[OK] dist folder doesn't exist (OK)" -ForegroundColor Green
}

# Step 2: Build React app
Write-Host ""
Write-Host "[2/3] Building React app..." -ForegroundColor Yellow
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Build failed! Check errors above." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Build completed" -ForegroundColor Green

# Step 3: Verify build output
Write-Host ""
Write-Host "[3/3] Verifying build output..." -ForegroundColor Yellow

if (Test-Path "dist/index.html") {
    Write-Host "[OK] dist/index.html exists" -ForegroundColor Green
} else {
    Write-Host "[ERROR] dist/index.html NOT FOUND!" -ForegroundColor Red
    exit 1
}

if (Test-Path "dist/assets") {
    $assetFiles = Get-ChildItem "dist/assets" -File
    if ($assetFiles.Count -gt 0) {
        Write-Host "[OK] dist/assets contains $($assetFiles.Count) files" -ForegroundColor Green
        Write-Host "  Sample files:" -ForegroundColor Gray
        $assetFiles | Select-Object -First 5 | ForEach-Object {
            Write-Host "    - $($_.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "[ERROR] dist/assets is EMPTY!" -ForegroundColor Red
        Write-Host "  Build may have failed. Check build output above." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "[ERROR] dist/assets NOT FOUND!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart FastAPI server" -ForegroundColor White
Write-Host "2. Visit http://127.0.0.1:8000/input_react" -ForegroundColor White
Write-Host "3. Check browser console for errors" -ForegroundColor White
