# RISKCAST API Guide

## Introduction

RISKCAST provides a comprehensive API for marine cargo insurance. This guide will help you get started with the most common operations.

## Authentication

All API requests require authentication. Include your API key in the header:

```bash
curl -H "X-API-Key: your_api_key" https://api.riskcast.io/api/v3/health/live
```

## Quick Start

### 1. Request a Quote

```python
from riskcast import RiskcastClient

client = RiskcastClient(api_key="your_api_key")

quote = client.quotes.request(
    origin_port="CNSHA",          # Shanghai
    destination_port="USLAX",      # Los Angeles
    cargo_type="ELECTRONICS",
    cargo_value_usd=500000,
    container_count=2,
    departure_date="2024-03-15",
    arrival_date="2024-04-05",
    coverage_type="ALL_RISKS"
)

print(f"Quote ID: {quote.id}")
print(f"Premium: ${quote.total_premium_usd:,.2f}")
print(f"Rate: ${quote.rate_per_mille}/1000")
print(f"Risk Grade: {quote.risk_grade}")
```

### 2. Accept a Quote

```python
# Accept the quote
accepted_quote = client.quotes.accept(quote.id)

print(f"Status: {accepted_quote.status}")  # ACCEPTED
```

### 3. Bind to Create Policy

```python
# Bind quote to create policy
policy = client.quotes.bind(quote.id)

print(f"Policy Number: {policy.policy_number}")
print(f"Effective From: {policy.effective_from}")
print(f"Effective To: {policy.effective_to}")
```

## Common Operations

### Risk Assessment

Get a risk assessment without creating a quote:

```python
assessment = client.risk.assess(
    origin_port="CNSHA",
    destination_port="USLAX",
    cargo_type="ELECTRONICS",
    cargo_value_usd=500000,
    departure_date="2024-03-15"
)

print(f"Risk Score: {assessment.overall_risk_score}")
print(f"Expected Loss: {assessment.expected_loss_pct}%")
```

### File a Claim

```python
claim = client.claims.file(
    policy_id="pol_123",
    loss_date="2024-03-20",
    loss_type="CARGO_DAMAGE",
    loss_description="Container fell during unloading",
    claimed_amount_usd=50000
)

print(f"Claim Number: {claim.claim_number}")
```

### Webhooks

Subscribe to events:

```python
webhook = client.webhooks.create(
    url="https://your-server.com/webhook",
    events=["quote.created", "policy.bound", "claim.filed"]
)

print(f"Webhook ID: {webhook.id}")
print(f"Secret: {webhook.secret}")  # Store this securely!
```

## Error Handling

```python
from riskcast import RiskcastClient, RateLimitError, ValidationError

client = RiskcastClient(api_key="your_api_key")

try:
    quote = client.quotes.request(...)
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Details: {e.details}")
```

## Rate Limits

| Tier | Requests/min | Requests/day |
|------|--------------|--------------|
| Starter | 100 | 10,000 |
| Professional | 500 | 100,000 |
| Enterprise | 2,000 | 1,000,000 |

## Port Codes

Use UN/LOCODE for ports:
- CNSHA - Shanghai
- USLAX - Los Angeles
- SGSIN - Singapore
- NLRTM - Rotterdam
- DEHAM - Hamburg

## Cargo Types

Supported cargo types:
- ELECTRONICS
- MACHINERY
- TEXTILES
- FOOD_PERISHABLE
- FOOD_DRY
- CHEMICALS
- PHARMACEUTICALS
- AUTOMOTIVE
- RAW_MATERIALS
- GENERAL

## Coverage Types

- ALL_RISKS - Comprehensive coverage
- NAMED_PERILS - Specific perils only
- TOTAL_LOSS_ONLY - Only total loss covered

## Support

- Documentation: https://docs.riskcast.io
- API Status: https://status.riskcast.io
- Email: support@riskcast.io
