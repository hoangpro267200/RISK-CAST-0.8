# Script kiểm tra tích hợp trang Results
# PowerShell script để verify tất cả components và integration

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KIỂM TRA TÍCH HỢP TRANG RESULTS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = @()
$warnings = @()
$success = @()

# 1. Kiểm tra Frontend Components
Write-Host "[1/8] Kiểm tra Frontend Components..." -ForegroundColor Yellow

$components = @(
    "src/pages/ResultsPage.tsx",
    "src/adapters/adaptResultV2.ts",
    "src/types/resultsViewModel.ts",
    "src/components/AlgorithmExplainabilityPanel.tsx",
    "src/components/InsuranceUnderwritingPanel.tsx",
    "src/components/LogisticsRealismPanel.tsx",
    "src/components/RiskDisclosurePanel.tsx"
)

foreach ($comp in $components) {
    if (Test-Path $comp) {
        $success += "✅ $comp"
    } else {
        $errors += "❌ Missing: $comp"
    }
}

# 2. Kiểm tra Hooks
Write-Host "[2/8] Kiểm tra Hooks..." -ForegroundColor Yellow

$hooks = @(
    "src/hooks/useUrlTabState.ts",
    "src/hooks/useExportResults.ts",
    "src/hooks/useChangeDetection.ts",
    "src/hooks/useAiDockState.tsx",
    "src/hooks/useKeyboardShortcuts.ts"
)

foreach ($hook in $hooks) {
    if (Test-Path $hook) {
        $success += "✅ $hook"
    } else {
        $errors += "❌ Missing: $hook"
    }
}

# 3. Kiểm tra Backend Files
Write-Host "[3/8] Kiểm tra Backend Files..." -ForegroundColor Yellow

$backendFiles = @(
    "app/main.py",
    "app/core/engine_state.py"
)

foreach ($file in $backendFiles) {
    if (Test-Path $file) {
        $success += "✅ $file"
        
        # Kiểm tra nội dung
        $content = Get-Content $file -Raw
        if ($file -like "*main.py" -and $content -match "get_results_data") {
            $success += "  ✅ /results/data endpoint found"
        } elseif ($file -like "*main.py" -and -not ($content -match "get_results_data")) {
            $warnings += "⚠️  /results/data endpoint not found in main.py"
        }
        
        if ($file -like "*engine_state.py" -and $content -match "get_last_result_v2") {
            $success += "  ✅ get_last_result_v2() function found"
        } elseif ($file -like "*engine_state.py" -and -not ($content -match "get_last_result_v2")) {
            $warnings += "⚠️  get_last_result_v2() not found in engine_state.py"
        }
    } else {
        $errors += "❌ Missing: $file"
    }
}

# 4. Kiểm tra Build Configuration
Write-Host "[4/8] Kiểm tra Build Configuration..." -ForegroundColor Yellow

if (Test-Path "vite.config.js") {
    $success += "✅ vite.config.js exists"
    $viteConfig = Get-Content "vite.config.js" -Raw
    if ($viteConfig -match "/results/data") {
        $success += "  ✅ Proxy configuration for /results/data"
    } else {
        $warnings += "⚠️  Proxy configuration for /results/data not found"
    }
} else {
    $errors += "❌ vite.config.js not found"
}

# 5. Kiểm tra package.json
Write-Host "[5/8] Kiểm tra package.json..." -ForegroundColor Yellow

if (Test-Path "package.json") {
    $success += "✅ package.json exists"
    $packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
    if ($packageJson.scripts.build) {
        $success += "  ✅ Build script found"
    } else {
        $warnings += "⚠️  Build script not found"
    }
} else {
    $errors += "❌ package.json not found"
}

# 6. Kiểm tra dist folder (nếu có)
Write-Host "[6/8] Kiểm tra Build Output..." -ForegroundColor Yellow

if (Test-Path "dist/index.html") {
    $success += "✅ dist/index.html exists (frontend built)"
} else {
    $warnings += "⚠️  dist/index.html not found - run 'npm run build' to build frontend"
}

# 7. Kiểm tra App.tsx routing
Write-Host "[7/8] Kiểm tra Routing..." -ForegroundColor Yellow

if (Test-Path "src/App.tsx") {
    $appContent = Get-Content "src/App.tsx" -Raw
    if ($appContent -match "ResultsPage") {
        $success += "✅ ResultsPage imported in App.tsx"
    } else {
        $errors += "❌ ResultsPage not found in App.tsx"
    }
    
    if ($appContent -match "/results") {
        $success += "✅ /results route handling found"
    } else {
        $warnings += "⚠️  /results route handling not explicit"
    }
} else {
    $errors += "❌ src/App.tsx not found"
}

# 8. Kiểm tra Type Definitions
Write-Host "[8/8] Kiểm tra Type Definitions..." -ForegroundColor Yellow

$typeFiles = @(
    "src/types/resultsViewModel.ts",
    "src/types/algorithmTypes.ts",
    "src/types/insuranceTypes.ts",
    "src/types/logisticsTypes.ts",
    "src/types/riskDisclosureTypes.ts"
)

foreach ($typeFile in $typeFiles) {
    if (Test-Path $typeFile) {
        $success += "✅ $typeFile"
    } else {
        $warnings += "⚠️  Optional type file not found: $typeFile"
    }
}

# Tổng kết
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KẾT QUẢ KIỂM TRA" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($success.Count -gt 0) {
    Write-Host "SUCCESS ($($success.Count) items):" -ForegroundColor Green
    foreach ($item in $success) {
        Write-Host "  $item" -ForegroundColor Green
    }
    Write-Host ""
}

if ($warnings.Count -gt 0) {
    Write-Host "WARNINGS ($($warnings.Count) items):" -ForegroundColor Yellow
    foreach ($item in $warnings) {
        Write-Host "  $item" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($errors.Count -gt 0) {
    Write-Host "ERRORS ($($errors.Count) items):" -ForegroundColor Red
    foreach ($item in $errors) {
        Write-Host "  $item" -ForegroundColor Red
    }
    Write-Host ""
}

# Tong ket cuoi cung
Write-Host "========================================" -ForegroundColor Cyan
if ($errors.Count -eq 0) {
    Write-Host "INTEGRATION COMPLETE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Build frontend: npm run build" -ForegroundColor White
    Write-Host "  2. Start backend: python dev_run.py" -ForegroundColor White
    Write-Host "  3. Access: http://localhost:8000/results" -ForegroundColor White
} else {
    Write-Host "ERRORS FOUND!" -ForegroundColor Red
    Write-Host "Please fix the errors above before continuing." -ForegroundColor Yellow
}
Write-Host "========================================" -ForegroundColor Cyan
