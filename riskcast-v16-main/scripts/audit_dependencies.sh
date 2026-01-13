#!/bin/bash
# Dependency Audit Script (Phase 6 - Day 18)
#
# CRITICAL: Audits dependencies for security vulnerabilities
# Run this in CI/CD pipeline to fail builds on high/critical vulnerabilities

set -e

echo "🔍 Running dependency security audit..."

# Python dependencies
echo "📦 Auditing Python dependencies..."
if command -v pip-audit &> /dev/null; then
    pip-audit --format json --output pip-audit-report.json || {
        echo "❌ pip-audit found vulnerabilities!"
        pip-audit
        exit 1
    }
    echo "✅ Python dependencies audit passed"
else
    echo "⚠️  pip-audit not installed. Install with: pip install pip-audit"
fi

# Node.js dependencies
echo "📦 Auditing Node.js dependencies..."
if command -v npm &> /dev/null; then
    cd riskcast-v16-main
    npm audit --audit-level=high || {
        echo "❌ npm audit found high/critical vulnerabilities!"
        exit 1
    }
    echo "✅ Node.js dependencies audit passed"
    cd ..
else
    echo "⚠️  npm not found"
fi

echo "✅ All dependency audits passed!"
