#!/bin/bash
# Archive Vue Summary Components Script
# This script moves Vue summary components to archive while keeping JS logic

set -e

echo "========================================"
echo "Archive Vue Summary Components"
echo "========================================"
echo ""

# Define paths
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
VUE_SUMMARY_DIR="$PROJECT_ROOT/src/features/risk-intelligence/components/summary"
ARCHIVE_DIR="$PROJECT_ROOT/archive/frontend/vue-summary-components"

# Check if Vue summary directory exists
if [ ! -d "$VUE_SUMMARY_DIR" ]; then
    echo "❌ Vue summary directory not found: $VUE_SUMMARY_DIR"
    exit 1
fi

# Check if Vue files exist
VUE_FILES=$(find "$VUE_SUMMARY_DIR" -name "*.vue" 2>/dev/null || true)
if [ -z "$VUE_FILES" ]; then
    echo "ℹ️  No Vue files found in summary directory. Nothing to archive."
    exit 0
fi

VUE_COUNT=$(echo "$VUE_FILES" | wc -l)
echo "Found $VUE_COUNT Vue component(s):"
echo "$VUE_FILES" | while read -r file; do
    echo "  - $(basename "$file")"
done
echo ""

# Create archive directory
echo "Creating archive directory..."
mkdir -p "$ARCHIVE_DIR"

# Create README in archive
cat > "$ARCHIVE_DIR/README.md" << EOF
# Vue Summary Components (Archived)

**Date Archived:** $(date +"%Y-%m-%d")
**Reason:** Summary page uses Vanilla JS business logic in \`app/static/js/summary/\`

## Business Logic Location

The summary page business logic is preserved in:
- **Core Controller:** \`app/static/js/summary/summary_controller.js\`
- **State Sync:** \`app/static/js/summary/summary_state_sync.js\`
- **Validator:** \`app/static/js/summary/summary_validator.js\`
- **Renderer:** \`app/static/js/summary/summary_renderer.js\`
- **Smart Editor:** \`app/static/js/summary/summary_smart_editor.js\`
- **Dataset Loader:** \`app/static/js/summary/summary_dataset_loader.js\`
- **Expert Rules:** \`app/static/js/summary/summary_expert_rules.js\`

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

$(echo "$VUE_FILES" | while read -r file; do
    echo "- $(basename "$file")"
done)
EOF

echo "✅ Created README in archive"
echo ""

# Move Vue files to archive
echo "Moving Vue components to archive..."
echo "$VUE_FILES" | while read -r file; do
    mv "$file" "$ARCHIVE_DIR/"
    echo "  ✓ Moved: $(basename "$file")"
done

echo ""
echo "========================================"
echo "✅ Archive Complete!"
echo "========================================"
echo ""
echo "Summary:"
echo "  - Archived: $VUE_COUNT Vue component(s)"
echo "  - Location: $ARCHIVE_DIR"
echo "  - JS Logic: Preserved in app/static/js/summary/"
echo ""
echo "Next steps:"
echo "  1. Test summary page: http://localhost:8000/summary"
echo "  2. Check for broken imports: grep -r 'RiskSummarySection' src/"
echo "  3. Commit changes: git add archive/ && git commit -m 'refactor: archive Vue summary components'"
echo ""

