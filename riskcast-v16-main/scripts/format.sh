#!/bin/bash
# RISKCAST Code Formatting Script (Unix/Linux/Mac)
# Formats Python and TypeScript/JavaScript code

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Formatting RISKCAST Code${NC}"
echo "================================"

# Python formatting (if black available)
if command -v black &> /dev/null; then
    echo -e "${YELLOW}Formatting Python with black...${NC}"
    black app/ --line-length=120 --exclude='/(venv|\.venv|__pycache__)/'
else
    echo -e "${YELLOW}black not installed, skipping Python format${NC}"
    echo "Install with: pip install black"
fi

# TypeScript/JavaScript formatting (if prettier available)
if command -v npm &> /dev/null && [ -f "package.json" ]; then
    if [ -d "node_modules" ]; then
        if npm list prettier &> /dev/null; then
            echo -e "${YELLOW}Formatting TypeScript/JS with prettier...${NC}"
            npx prettier --write "src/**/*.{ts,tsx,js,jsx}" || true
        else
            echo -e "${YELLOW}prettier not installed, skipping TypeScript/JS format${NC}"
            echo "Install with: npm install --save-dev prettier"
        fi
    else
        echo -e "${YELLOW}node_modules not found. Run 'npm install' first${NC}"
    fi
else
    echo -e "${YELLOW}npm not available, skipping TypeScript/JS format${NC}"
fi

echo -e "${GREEN}Formatting completed!${NC}"

