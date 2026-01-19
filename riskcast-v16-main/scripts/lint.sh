#!/bin/bash
# RISKCAST Linting Script (Unix/Linux/Mac)
# Runs linting for both Python and TypeScript/JavaScript

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running RISKCAST Linters${NC}"
echo "================================"

# Python linting (if flake8/ruff available)
if command -v flake8 &> /dev/null; then
    echo -e "${YELLOW}Running flake8...${NC}"
    flake8 app/ --max-line-length=120 --exclude=__pycache__,venv,.venv || true
elif command -v ruff &> /dev/null; then
    echo -e "${YELLOW}Running ruff...${NC}"
    ruff check app/ || true
else
    echo -e "${YELLOW}flake8/ruff not installed, skipping Python lint${NC}"
    echo "Install with: pip install flake8 or pip install ruff"
fi

# TypeScript/JavaScript linting (if eslint available)
if command -v npm &> /dev/null && [ -f "package.json" ]; then
    if [ -d "node_modules" ]; then
        echo -e "${YELLOW}Running ESLint...${NC}"
        npm run lint || true
    else
        echo -e "${YELLOW}node_modules not found. Run 'npm install' first${NC}"
    fi
else
    echo -e "${YELLOW}npm not available, skipping TypeScript/JS lint${NC}"
fi

echo -e "${GREEN}Linting completed!${NC}"

