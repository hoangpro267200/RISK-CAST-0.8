#!/bin/bash

# Run Pact contract tests

set -e

echo "=== Running Contract Tests ==="

# Create directories
mkdir -p pacts pact_logs

# Run consumer tests
echo "Running consumer contract tests..."
pytest tests/contract/test_quote_contracts.py -v
pytest tests/contract/test_policy_contracts.py -v
pytest tests/contract/test_claims_contracts.py -v
pytest tests/contract/test_external_service_contracts.py -v

# Publish pacts to broker (if available)
if [ -n "$PACT_BROKER_URL" ]; then
    echo "Publishing pacts to broker..."
    pact-broker publish ./pacts \
        --broker-base-url=$PACT_BROKER_URL \
        --consumer-app-version=$(git rev-parse --short HEAD 2>/dev/null || echo "dev") \
        --tag=$(git branch --show-current 2>/dev/null || echo "main")
fi

# Run provider verification (if API is running)
if [ -n "$API_URL" ]; then
    echo "Running provider verification..."
    pytest tests/contract/test_provider_verification.py -v
fi

echo "=== Contract Tests Complete ==="
