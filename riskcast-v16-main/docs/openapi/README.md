# OpenAPI Specification

This directory contains the OpenAPI 3.1.0 specification for the RISKCAST V3 API.

## Files

- `openapi.yaml` - Complete OpenAPI specification for all API v3 endpoints

## Usage

### View in Swagger UI

1. Install Swagger UI:
```bash
npm install -g swagger-ui-serve
```

2. Serve the spec:
```bash
swagger-ui-serve docs/openapi/openapi.yaml
```

3. Open http://localhost:3000 in your browser

### Generate Client SDKs

#### Python
```bash
openapi-generator generate -i docs/openapi/openapi.yaml -g python -o clients/python
```

#### TypeScript
```bash
openapi-generator generate -i docs/openapi/openapi.yaml -g typescript-axios -o clients/typescript
```

#### JavaScript
```bash
openapi-generator generate -i docs/openapi/openapi.yaml -g javascript -o clients/javascript
```

### Validate Specification

```bash
# Using swagger-cli
npm install -g @apidevtools/swagger-cli
swagger-cli validate docs/openapi/openapi.yaml

# Using openapi-validator
npm install -g openapi-validator
openapi-validator docs/openapi/openapi.yaml
```

## API Documentation

### Base URL

- **Production**: `https://api.riskcast.com/api/v3`
- **Staging**: `https://staging-api.riskcast.com/api/v3`
- **Local**: `http://localhost:8000/api/v3`

### Authentication

All endpoints require JWT authentication:

```http
Authorization: Bearer <your-jwt-token>
```

### Rate Limits

- Standard: 100 requests/minute
- Authenticated: 1000 requests/minute

### Endpoints

#### Risk Assessment
- `POST /risk-assessments` - Create risk assessment
- `GET /risk-assessments` - List assessments
- `GET /risk-assessments/{id}` - Get assessment
- `POST /risk-assessments/{id}/runs` - Queue risk run

#### Risk Runs
- `GET /risk-runs` - List runs
- `GET /risk-runs/{id}` - Get run details

#### Underwriting
- `POST /underwriting/submissions` - Create submission
- `GET /underwriting/submissions` - List submissions
- `GET /underwriting/submissions/{id}` - Get submission
- `POST /underwriting/submissions/{id}/decisions` - Make decision

#### Policies
- `POST /policies/bind` - Bind policy
- `GET /policies/{id}` - Get policy
- `GET /policies/{id}/verify` - Verify integrity
- `GET /policies/{id}/decision-pack` - Download decision pack

#### Claims
- `POST /claims` - File claim (FNOL)
- `GET /claims` - List claims
- `GET /claims/{id}` - Get claim
- `POST /claims/{id}/adjudicate` - Adjudicate claim
- `POST /claims/{id}/authorize` - Authorize payout
- `GET /claims/{id}/history` - Get claim history

#### Evidence
- `POST /evidence/bundles` - Create bundle
- `POST /evidence/bundles/{id}/seal` - Seal bundle
- `GET /evidence/bundles/{id}/verify` - Verify integrity

#### Models
- `GET /models` - List model versions
- `POST /models/{id}/publish` - Publish model

#### Analytics
- `GET /analytics/loss-ratio` - Get loss ratio
- `GET /analytics/model-performance/{id}` - Get model performance

#### Compliance
- `POST /compliance/gdpr/export` - Export user data
- `POST /compliance/gdpr/delete` - Delete user data

## Permissions

Each endpoint requires specific RBAC permissions:

- `RISK_READ`, `RISK_WRITE`, `RISK_RUN` - Risk assessment operations
- `UNDERWRITING_READ`, `UNDERWRITING_WRITE`, `UNDERWRITING_DECIDE` - Underwriting operations
- `POLICY_READ`, `POLICY_WRITE` - Policy operations
- `claim:read`, `claim:write`, `claim:adjudicate`, `claim:authorize` - Claims operations
- `EVIDENCE_READ`, `EVIDENCE_WRITE` - Evidence operations
- `MODEL_READ`, `MODEL_WRITE` - Model operations
- `analytics:read` - Analytics operations
- `COMPLIANCE_READ`, `COMPLIANCE_WRITE` - Compliance operations

## Examples

### Create Risk Assessment

```bash
curl -X POST https://api.riskcast.com/api/v3/risk-assessments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "shipment": {
      "cargo_type": "ELECTRONICS",
      "cargo_value_usd": 500000,
      "container_count": 10,
      "packaging_quality": "EXCELLENT"
    },
    "route": {
      "origin_port": "CNSHA",
      "destination_port": "NLRTM",
      "carrier_code": "MAEU"
    },
    "coverage": {
      "coverage_type": "ALL_RISK",
      "insured_value_cents": 50000000,
      "currency": "USD"
    }
  }'
```

### File Claim

```bash
curl -X POST "https://api.riskcast.com/api/v3/claims?policy_id=<policy-id>" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "loss_date": "2024-01-15T10:00:00Z",
    "loss_description": "Container damaged during transit",
    "loss_amount_cents": 5000000,
    "location": "Port of Rotterdam"
  }'
```

## Updates

The OpenAPI spec is maintained manually and should be updated when:
- New endpoints are added
- Request/response schemas change
- Authentication methods change
- Error responses change

## Validation

The spec is validated in CI/CD pipeline using:
- `swagger-cli validate`
- OpenAPI Generator for client SDK generation

## See Also

- [API Documentation](../API_DOCUMENTATION.md)
- [V3 API Endpoints Complete](../../V3_API_ENDPOINTS_COMPLETE.md)
- [Authentication System](../../docs/AUTH_SYSTEM.md)
