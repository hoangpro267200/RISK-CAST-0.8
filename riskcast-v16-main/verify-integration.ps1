# Integration Verification Script
# Checks that all Sprint components are properly integrated

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RISKCAST RESULTS PAGE INTEGRATION CHECK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# Check 1: Sprint 1 Components
Write-Host "[1/6] Checking Sprint 1 Components..." -ForegroundColor Yellow

$sprint1Files = @(
    "src/components/AlgorithmExplainabilityPanel.tsx",
    "src/components/FAHPWeightChart.tsx",
    "src/components/TOPSISBreakdown.tsx",
    "src/components/MonteCarloExplainer.tsx",
    "src/services/narrativeGenerator.ts",
    "src/types/algorithmTypes.ts"
)

foreach ($file in $sprint1Files) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $file" -ForegroundColor Red
        $errors++
    }
}

# Check 2: Sprint 2 Components
Write-Host ""
Write-Host "[2/6] Checking Sprint 2 Components..." -ForegroundColor Yellow

$sprint2Files = @(
    "src/components/InsuranceUnderwritingPanel.tsx",
    "src/components/LossDistributionHistogram.tsx",
    "src/components/BasisRiskScore.tsx",
    "src/components/TriggerProbabilityTable.tsx",
    "src/components/CoverageRecommendations.tsx",
    "src/components/PremiumLogicExplainer.tsx",
    "src/components/ExclusionsDisclosure.tsx",
    "src/components/DeductibleRecommendation.tsx",
    "src/components/LogisticsRealismPanel.tsx",
    "src/components/CargoContainerValidation.tsx",
    "src/components/RouteSeasonalityRisk.tsx",
    "src/components/PortCongestionStatus.tsx",
    "src/components/InsuranceAttentionFlags.tsx",
    "src/types/insuranceTypes.ts",
    "src/types/logisticsTypes.ts"
)

foreach ($file in $sprint2Files) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $file" -ForegroundColor Red
        $errors++
    }
}

# Check 3: Sprint 3 Components
Write-Host ""
Write-Host "[3/6] Checking Sprint 3 Components..." -ForegroundColor Yellow

$sprint3Files = @(
    "src/components/RiskDisclosurePanel.tsx",
    "src/components/LatentRisksTable.tsx",
    "src/components/TailEventsExplainer.tsx",
    "src/components/ActionableMitigations.tsx",
    "src/components/FactorContributionWaterfall.tsx",
    "src/types/riskDisclosureTypes.ts"
)

foreach ($file in $sprint3Files) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $file" -ForegroundColor Red
        $errors++
    }
}

# Check 4: ResultsPage Integration
Write-Host ""
Write-Host "[4/6] Checking ResultsPage Integration..." -ForegroundColor Yellow

$resultsPage = "src/pages/ResultsPage.tsx"
if (Test-Path $resultsPage) {
    $content = Get-Content $resultsPage -Raw
    
    $requiredImports = @(
        "AlgorithmExplainabilityPanel",
        "InsuranceUnderwritingPanel",
        "LogisticsRealismPanel",
        "RiskDisclosurePanel",
        "FactorContributionWaterfall"
    )
    
    foreach ($import in $requiredImports) {
        if ($content -match $import) {
            Write-Host "  ✓ $import imported" -ForegroundColor Green
        } else {
            Write-Host "  ✗ MISSING: $import not found in ResultsPage" -ForegroundColor Red
            $errors++
        }
    }
    
    # Check usage
    if ($content -match "AlgorithmExplainabilityPanel.*algorithmData") {
        Write-Host "  ✓ AlgorithmExplainabilityPanel used" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ AlgorithmExplainabilityPanel may not be used" -ForegroundColor Yellow
        $warnings++
    }
    
    if ($content -match "InsuranceUnderwritingPanel") {
        Write-Host "  ✓ InsuranceUnderwritingPanel used" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ InsuranceUnderwritingPanel may not be used" -ForegroundColor Yellow
        $warnings++
    }
    
    if ($content -match "LogisticsRealismPanel") {
        Write-Host "  ✓ LogisticsRealismPanel used" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ LogisticsRealismPanel may not be used" -ForegroundColor Yellow
        $warnings++
    }
    
    if ($content -match "RiskDisclosurePanel") {
        Write-Host "  ✓ RiskDisclosurePanel used" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ RiskDisclosurePanel may not be used" -ForegroundColor Yellow
        $warnings++
    }
    
    if ($content -match "FactorContributionWaterfall") {
        Write-Host "  ✓ FactorContributionWaterfall used" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ FactorContributionWaterfall may not be used" -ForegroundColor Yellow
        $warnings++
    }
} else {
    Write-Host "  ✗ ResultsPage.tsx not found!" -ForegroundColor Red
    $errors++
}

# Check 5: Adapter Integration
Write-Host ""
Write-Host "[5/6] Checking Adapter Integration..." -ForegroundColor Yellow

$adapter = "src/adapters/adaptResultV2.ts"
if (Test-Path $adapter) {
    $content = Get-Content $adapter -Raw
    
    if ($content -match "riskDisclosure") {
        Write-Host "  ✓ riskDisclosure extraction in adapter" -ForegroundColor Green
    } else {
        Write-Host "  ✗ riskDisclosure extraction missing in adapter" -ForegroundColor Red
        $errors++
    }
    
    if ($content -match "algorithm.*fahp|fahp.*weights") {
        Write-Host "  ✓ FAHP data extraction in adapter" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ FAHP extraction may be incomplete" -ForegroundColor Yellow
        $warnings++
    }
    
    if ($content -match "insurance.*lossDistribution|lossDistribution") {
        Write-Host "  ✓ Insurance data extraction in adapter" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Insurance extraction may be incomplete" -ForegroundColor Yellow
        $warnings++
    }
    
    if ($content -match "logistics.*cargoContainer|cargoContainer") {
        Write-Host "  ✓ Logistics data extraction in adapter" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Logistics extraction may be incomplete" -ForegroundColor Yellow
        $warnings++
    }
} else {
    Write-Host "  ✗ adaptResultV2.ts not found!" -ForegroundColor Red
    $errors++
}

# Check 6: Type Definitions
Write-Host ""
Write-Host "[6/6] Checking Type Definitions..." -ForegroundColor Yellow

$typeFiles = @(
    "src/types/resultsViewModel.ts",
    "src/types/algorithmTypes.ts",
    "src/types/insuranceTypes.ts",
    "src/types/logisticsTypes.ts",
    "src/types/riskDisclosureTypes.ts"
)

foreach ($file in $typeFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $file" -ForegroundColor Red
        $errors++
    }
}

# Final Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($errors -eq 0 -and $warnings -eq 0) {
    Write-Host "✓ ALL CHECKS PASSED" -ForegroundColor Green
    Write-Host ""
    Write-Host "Integration Status: READY" -ForegroundColor Green
    exit 0
} elseif ($errors -eq 0) {
    Write-Host "✓ ALL CRITICAL CHECKS PASSED" -ForegroundColor Green
    Write-Host "⚠ Warnings: $warnings" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Integration Status: READY (with warnings)" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "✗ ERRORS FOUND: $errors" -ForegroundColor Red
    if ($warnings -gt 0) {
        Write-Host "⚠ Warnings: $warnings" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Integration Status: NEEDS FIXES" -ForegroundColor Red
    exit 1
}
