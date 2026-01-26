# Pact Contract Testing

Contract testing framework using Pact to ensure API compatibility between services.

## Overview

This module provides contract tests for:
- **Consumer Tests**: Define expected API contracts from consumer perspective
- **Provider Verification**: Verify that the API satisfies all consumer contracts
- **External Service Contracts**: Test contracts with external dependencies

## Architecture

### Consumers

- **QuotePortal**: Frontend application consuming Quote API
- **PolicyDashboard**: Policy management dashboard
- **ClaimsPortal**: Claims management portal

### Provider

- **RiskCastAPI**: Main RiskCast API (provider)

### External Services (RiskCast as Consumer)

- **TomorrowIO**: Weather API
- **MarineTraffic**: Vessel tracking API

## Setup

### 1. Install Dependencies

```bash
pip install pact-python
```

### 2. Install Pact CLI (Optional)

For publishing to Pact Broker:

```bash
# macOS/Linux
brew install pact-foundation/pact/pact-cli

# Or download from: https://github.com/pact-foundation/pact-ruby-standalone/releases
```

### 3. Start Pact Broker (Optional)

```bash
docker run -d -p 9292:9292 pactfoundation/pact-broker
```

## Running Tests

### Consumer Tests

```bash
# Run all consumer tests
pytest tests/contract/test_quote_contracts.py -v
pytest tests/contract/test_policy_contracts.py -v
pytest tests/contract/test_claims_contracts.py -v

# Or use the script
./scripts/run_contract_tests.sh
```

### Provider Verification

```bash
# Set API URL
export API_URL=http://localhost:8000

# Run verification
pytest tests/contract/test_provider_verification.py -v
```

### Publish to Broker

```bash
export PACT_BROKER_URL=http://localhost:9292
export PACT_BROKER_TOKEN=your-token

pact-broker publish ./pacts \
    --broker-base-url=$PACT_BROKER_URL \
    --consumer-app-version=$(git rev-parse --short HEAD) \
    --tag=$(git branch --show-current)
```

## Test Structure

### Consumer Tests

Consumer tests define the expected contract:

```python
(pact_consumer
    .given("a valid user is authenticated")
    .upon_receiving("a request to create a quote")
    .with_request(method="POST", path="/api/v3/quotes", ...)
    .will_respond_with(status=201, body=expected_response))
```

### Provider Verification

Provider verification tests ensure the API satisfies contracts:

```python
verifier = Verifier(provider="RiskCastAPI", provider_base_url=api_url)
verifier.set_state_handler("a valid user is authenticated", setup_handler)
verifier.verify_pacts(pact_url)
```

## Provider States

Provider states set up test data:

- `a valid user is authenticated`: Create authenticated user
- `quote qt_abc123 exists`: Create quote in database
- `quote qt_abc123 is pending and valid`: Set quote to pending status
- `user has quotes`: Create quotes for user
- `policy pol_xyz789 exists and is active`: Create active policy
- `policy pol_xyz789 is active and cancellable`: Set policy to cancellable state
- `user has active policies`: Create active policies for user

## Pact Matchers

Use Pact matchers for flexible matching:

- `Like(value)`: Matches any value of the same type
- `Term(regex, example)`: Matches regex pattern
- `EachLike(item)`: Matches array with at least one item
- `Format(format_string)`: Matches format (email, date, etc.)

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Contract Tests
  run: |
    pytest tests/contract/ -v
    
- name: Publish Pacts
  if: github.ref == 'refs/heads/main'
  run: |
    pact-broker publish ./pacts \
      --broker-base-url=${{ secrets.PACT_BROKER_URL }} \
      --consumer-app-version=${{ github.sha }} \
      --tag=${{ github.ref_name }}
```

## Best Practices

1. **Version Contracts**: Use semantic versioning for contracts
2. **Provider States**: Implement state handlers for all provider states
3. **Matchers**: Use appropriate matchers (Like, Term) for flexibility
4. **Broker Integration**: Publish pacts to broker for team collaboration
5. **CI Integration**: Run contract tests in CI/CD pipeline
6. **Breaking Changes**: Use Pact's can-i-deploy to check compatibility

## Troubleshooting

### Pact Service Not Starting

- Check if ports are available (1234, 1235, 1236, etc.)
- Ensure pact-python is installed correctly
- Check logs in `pact_logs/` directory

### Verification Failures

- Ensure API is running and accessible
- Check provider state handlers are implemented
- Verify API responses match contract expectations

### Broker Connection Issues

- Verify PACT_BROKER_URL is correct
- Check authentication token if required
- Ensure broker is accessible from CI/CD environment

## Resources

- [Pact Documentation](https://docs.pact.io/)
- [Pact Python](https://github.com/pact-foundation/pact-python)
- [Pact Broker](https://github.com/pact-foundation/pact_broker)
