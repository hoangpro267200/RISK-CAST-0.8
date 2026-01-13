# Archive Vue Summary Components Script
# This script moves Vue summary components to archive while keeping JS logic

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Archive Vue Summary Components" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define paths
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VueSummaryDir = Join-Path $ProjectRoot "src\features\risk-intelligence\components\summary"
$ArchiveDir = Join-Path $ProjectRoot "archive\frontend\vue-summary-components"

# Check if Vue summary directory exists
if (-not (Test-Path $VueSummaryDir)) {
    Write-Host "❌ Vue summary directory not found: $VueSummaryDir" -ForegroundColor Red
    exit 1
}

# Check if Vue files exist
$VueFiles = Get-ChildItem -Path $VueSummaryDir -Filter "*.vue" -ErrorAction SilentlyContinue
if ($VueFiles.Count -eq 0) {
    Write-Host "ℹ️  No Vue files found in summary directory. Nothing to archive." -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($VueFiles.Count) Vue component(s):" -ForegroundColor Green
$VueFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
Write-Host ""

# Create archive directory
Write-Host "Creating archive directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $ArchiveDir -Force | Out-Null

# Create README in archive
$ReadmeContent = @"
# Vue Summary Components (Archived)

**Date Archived:** $(Get-Date -Format "yyyy-MM-dd")
**Reason:** Summary page uses Vanilla JS business logic in `app/static/js/summary/`

## Business Logic Location

The summary page business logic is preserved in:
- **Core Controller:** `app/static/js/summary/summary_controller.js`
- **State Sync:** `app/static/js/summary/summary_state_sync.js`
- **Validator:** `app/static/js/summary/summary_validator.js`
- **Renderer:** `app/static/js/summary/summary_renderer.js`
- **Smart Editor:** `app/static/js/summary/summary_smart_editor.js`
- **Dataset Loader:** `app/static/js/summary/summary_dataset_loader.js`
- **Expert Rules:** `app/static/js/summary/summary_expert_rules.js`

## Why Archived?

1. **Vue components are UI-only** - No business logic
2. **JS logic is core** - Cannot be replaced
3. **Frontend strategy** - React + TypeScript is canonical
4. **Vue is legacy** - Maintain but don't extend

## Restoration

If needed, these components can be restored from git history:
\`\`\`bash
git checkout HEAD~1 -- src/features/risk-intelligence/components/summary/*.vue
\`\`\`

## Components Archived

$($VueFiles | ForEach-Object { "- $($_.Name)" } | Out-String)
"@

$ReadmePath = Join-Path $ArchiveDir "README.md"
$ReadmeContent | Out-File -FilePath $ReadmePath -Encoding UTF8

Write-Host "✅ Created README in archive" -ForegroundColor Green
Write-Host ""

# Move Vue files to archive
Write-Host "Moving Vue components to archive..." -ForegroundColor Yellow
$VueFiles | ForEach-Object {
    $DestPath = Join-Path $ArchiveDir $_.Name
    Move-Item -Path $_.FullName -Destination $DestPath -Force
    Write-Host "  ✓ Moved: $($_.Name)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Archive Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - Archived: $($VueFiles.Count) Vue component(s)" -ForegroundColor White
Write-Host "  - Location: $ArchiveDir" -ForegroundColor White
Write-Host "  - JS Logic: Preserved in app/static/js/summary/" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test summary page: http://localhost:8000/summary" -ForegroundColor White
Write-Host "  2. Check for broken imports: grep -r 'RiskSummarySection' src/" -ForegroundColor White
Write-Host "  3. Commit changes: git add archive/ && git commit -m 'refactor: archive Vue summary components'" -ForegroundColor White
Write-Host ""

