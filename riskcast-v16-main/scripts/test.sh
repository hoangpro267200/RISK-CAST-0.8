#!/bin/bash
# RISKCAST Test Runner Script (Unix/Linux/Mac)
# Run tests with proper configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Running RISKCAST Tests${NC}"
echo "================================"

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-cov"
    exit 1
fi

# Run tests
echo -e "${YELLOW}Running unit tests...${NC}"
python -m pytest tests/unit/ -v --tb=short

echo -e "${YELLOW}Running integration tests...${NC}"
python -m pytest tests/integration/ -v --tb=short

# Run with coverage if pytest-cov is installed
if python -m pytest --collect-only -q 2>&1 | grep -q "pytest-cov"; then
    echo -e "${YELLOW}Running with coverage...${NC}"
    python -m pytest tests/ --cov=app --cov-report=term --cov-report=html --tb=short
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
else
    echo -e "${YELLOW}pytest-cov not installed, skipping coverage${NC}"
    echo "Install with: pip install pytest-cov"
fi

echo -e "${GREEN}Tests completed!${NC}"

