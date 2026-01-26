@echo off
REM Run Pact contract tests (Windows)

echo === Running Contract Tests ===

REM Create directories
if not exist pacts mkdir pacts
if not exist pact_logs mkdir pact_logs

REM Run consumer tests
echo Running consumer contract tests...
pytest tests\contract\test_quote_contracts.py -v
pytest tests\contract\test_policy_contracts.py -v
pytest tests\contract\test_claims_contracts.py -v
pytest tests\contract\test_external_service_contracts.py -v

REM Publish pacts to broker (if available)
if defined PACT_BROKER_URL (
    echo Publishing pacts to broker...
    pact-broker publish .\pacts --broker-base-url=%PACT_BROKER_URL% --consumer-app-version=dev --tag=main
)

REM Run provider verification (if API is running)
if defined API_URL (
    echo Running provider verification...
    pytest tests\contract\test_provider_verification.py -v
)

echo === Contract Tests Complete ===
pause
