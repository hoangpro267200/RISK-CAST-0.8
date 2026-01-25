#!/bin/bash
# =============================================================================
# Smoke Test Script
# =============================================================================
#
# Tests basic functionality of the deployed API
#
# Usage:
#   ./smoke-test.sh <base-url>
#
# Example:
#   ./smoke-test.sh https://api.riskcast.io
#   ./smoke-test.sh http://localhost:8000

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-http://localhost:8000}"
TIMEOUT=10
FAILED_TESTS=0
PASSED_TESTS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}RiskCast API Smoke Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Base URL: ${YELLOW}$BASE_URL${NC}"
echo -e "Timeout: ${TIMEOUT}s"
echo ""

# ===========================================================================
# Helper Functions
# ===========================================================================

test_endpoint() {
    local name="$1"
    local path="$2"
    local expected_status="${3:-200}"
    local method="${4:-GET}"
    
    echo -n "Testing ${name}... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time $TIMEOUT \
        -X "$method" \
        "$BASE_URL$path" 2>&1)
    
    if [ "$response" == "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response, expected $expected_status)"
        ((FAILED_TESTS++))
        return 1
    fi
}

test_json_response() {
    local name="$1"
    local path="$2"
    local json_key="$3"
    
    echo -n "Testing ${name}... "
    
    response=$(curl -s --max-time $TIMEOUT "$BASE_URL$path" 2>&1)
    
    if echo "$response" | jq -e ".$json_key" > /dev/null 2>&1; then
        value=$(echo "$response" | jq -r ".$json_key")
        echo -e "${GREEN}✓ OK${NC} (${json_key}=${value})"
        ((PASSED_TESTS++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (key '$json_key' not found in response)"
        ((FAILED_TESTS++))
        return 1
    fi
}

# ===========================================================================
# Health Checks
# ===========================================================================

echo -e "${BLUE}Health Checks${NC}"
echo "----------------------------------------"

test_endpoint "Liveness probe" "/health/live" 200
test_endpoint "Readiness probe" "/health/ready" 200

if command -v jq &> /dev/null; then
    test_json_response "Health status" "/health/live" "status"
fi

echo ""

# ===========================================================================
# API Endpoints
# ===========================================================================

echo -e "${BLUE}API Endpoints${NC}"
echo "----------------------------------------"

# OpenAPI documentation
test_endpoint "OpenAPI spec" "/openapi.json" 200

# API documentation (might be disabled in production)
test_endpoint "API docs" "/docs" "200|404"

# API v3 health
test_endpoint "API v3 health" "/api/v3/health" 200

echo ""

# ===========================================================================
# Metrics
# ===========================================================================

echo -e "${BLUE}Observability${NC}"
echo "----------------------------------------"

test_endpoint "Metrics endpoint" "/metrics" 200

echo ""

# ===========================================================================
# Performance Test
# ===========================================================================

echo -e "${BLUE}Performance${NC}"
echo "----------------------------------------"

echo -n "Testing response time... "
start_time=$(date +%s%N)
curl -s -o /dev/null --max-time $TIMEOUT "$BASE_URL/health/live"
end_time=$(date +%s%N)
duration=$(( (end_time - start_time) / 1000000 ))

if [ $duration -lt 1000 ]; then
    echo -e "${GREEN}✓ OK${NC} (${duration}ms)"
    ((PASSED_TESTS++))
elif [ $duration -lt 3000 ]; then
    echo -e "${YELLOW}⚠ SLOW${NC} (${duration}ms)"
    ((PASSED_TESTS++))
else
    echo -e "${RED}✗ TOO SLOW${NC} (${duration}ms)"
    ((FAILED_TESTS++))
fi

echo ""

# ===========================================================================
# Security Headers (Optional)
# ===========================================================================

echo -e "${BLUE}Security Headers${NC}"
echo "----------------------------------------"

echo -n "Testing security headers... "
headers=$(curl -s -I --max-time $TIMEOUT "$BASE_URL/health/live")

if echo "$headers" | grep -qi "x-content-type-options"; then
    echo -e "${GREEN}✓ OK${NC} (X-Content-Type-Options present)"
    ((PASSED_TESTS++))
else
    echo -e "${YELLOW}⚠ WARNING${NC} (X-Content-Type-Options missing)"
fi

echo ""

# ===========================================================================
# Summary
# ===========================================================================

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"

TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS))

echo -e "Total tests: ${TOTAL_TESTS}"
echo -e "Passed: ${GREEN}${PASSED_TESTS}${NC}"
echo -e "Failed: ${RED}${FAILED_TESTS}${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed!${NC}"
    exit 1
fi
