# Sprint 1 Files Verification Script
# Run this script to verify all Sprint 1 files exist

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SPRINT 1 FILES VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$basePath = "src"
$allFilesExist = $true

# Type Files
Write-Host "Checking Type Files..." -ForegroundColor Yellow
$typeFiles = @(
    "$basePath/types/algorithmTypes.ts",
    "$basePath/types/insuranceTypes.ts",
    "$basePath/types/logisticsTypes.ts",
    "$basePath/types/riskDisclosureTypes.ts"
)

foreach ($file in $typeFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file - MISSING" -ForegroundColor Red
        $allFilesExist = $false
    }
}

# Component Files
Write-Host ""
Write-Host "Checking Component Files..." -ForegroundColor Yellow
$componentFiles = @(
    "$basePath/components/FAHPWeightChart.tsx",
    "$basePath/components/TOPSISBreakdown.tsx",
    "$basePath/components/MonteCarloExplainer.tsx",
    "$basePath/components/AlgorithmExplainabilityPanel.tsx"
)

foreach ($file in $componentFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file - MISSING" -ForegroundColor Red
        $allFilesExist = $false
    }
}

# Service Files
Write-Host ""
Write-Host "Checking Service Files..." -ForegroundColor Yellow
$serviceFiles = @(
    "$basePath/services/narrativeGenerator.ts"
)

foreach ($file in $serviceFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file - MISSING" -ForegroundColor Red
        $allFilesExist = $false
    }
}

# Modified Files
Write-Host ""
Write-Host "Checking Modified Files..." -ForegroundColor Yellow
$modifiedFiles = @(
    "$basePath/types/resultsViewModel.ts",
    "$basePath/adapters/adaptResultV2.ts",
    "$basePath/pages/ResultsPage.tsx"
)

foreach ($file in $modifiedFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file - MISSING" -ForegroundColor Red
        $allFilesExist = $false
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allFilesExist) {
    Write-Host "ALL FILES EXIST" -ForegroundColor Green
    Write-Host "Sprint 1 files verification: PASSED" -ForegroundColor Green
} else {
    Write-Host "SOME FILES MISSING" -ForegroundColor Red
    Write-Host "Sprint 1 files verification: FAILED" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan
