# RISKCAST Data Partnership Agreement Template

## PARTNERSHIP OVERVIEW

### Partnership Model: Data-for-Value Exchange

This template outlines the framework for data partnerships that enable RISKCAST to improve model accuracy while providing partners with enhanced risk intelligence capabilities.

---

## PARTNERSHIP VALUE PROPOSITION

### What Partners Contribute

1. **Historical Shipment Data**
   - Minimum: 500 shipments with outcomes
   - Target: 2,000+ shipments for full calibration
   - Data elements: Routes, carriers, cargo, dates, outcomes

2. **Outcome Data (Critical)**
   - Actual delays (duration, cause)
   - Cargo incidents (loss, damage, severity)
   - Claims data (if available)
   - Resolution details

3. **Operational Context**
   - Route-specific challenges
   - Carrier performance insights
   - Seasonal patterns
   - Market dynamics

### What RISKCAST Provides

1. **Platform Access**
   - Free or discounted subscription (based on data volume)
   - Priority feature access
   - Extended API limits

2. **Custom Calibration**
   - Model tuned to partner's specific routes/commodities
   - Higher accuracy for partner's use cases
   - Exclusive regional insights

3. **Support & Development**
   - Priority support queue
   - Feature request prioritization
   - Dedicated success manager

4. **Marketing Value**
   - Co-branded case studies (with approval)
   - Joint press releases
   - Conference speaking opportunities

---

## PARTNERSHIP TIERS

### Tier 1: Strategic Partner

**Data Contribution**: 5,000+ shipments annually
**Value Exchange**:
- Enterprise license (100% discount)
- Exclusive regional calibration
- Board advisory seat (optional)
- Co-development rights

### Tier 2: Premium Partner

**Data Contribution**: 2,000-5,000 shipments annually
**Value Exchange**:
- Professional license (75% discount)
- Dedicated calibration
- Priority support
- Quarterly business reviews

### Tier 3: Growth Partner

**Data Contribution**: 500-2,000 shipments annually
**Value Exchange**:
- Professional license (50% discount)
- Standard calibration inclusion
- Priority support
- Annual review

### Tier 4: Pilot Partner

**Data Contribution**: 500 shipments (one-time)
**Value Exchange**:
- 6-month professional trial
- Pilot calibration
- Case study participation
- Conversion to Tier 3+ upon expansion

---

## DATA SPECIFICATIONS

### Required Fields (Minimum)

```yaml
Shipment Data:
  - shipment_id: string (unique identifier)
  - origin_port: string (UN/LOCODE or equivalent)
  - destination_port: string
  - departure_date: date (ISO 8601)
  - arrival_date: date (actual)
  - transport_mode: string (ocean/air/rail/road)
  - carrier: string (carrier name or code)
  - cargo_type: string
  - cargo_value_usd: float
  - container_type: string (if applicable)
  
Outcome Data:
  - delay_days: integer (actual vs scheduled)
  - incident_type: string (none/delay/damage/loss)
  - incident_severity: float (0-1 scale or category)
  - incident_cause: string (if known)
  - claim_amount_usd: float (if applicable)
```

### Optional Fields (Preferred)

```yaml
Enhanced Data:
  - weather_conditions: string
  - port_congestion_level: string
  - customs_clearance_time: float (hours)
  - transshipment_count: integer
  - packaging_type: string
  - temperature_controlled: boolean
  - hazmat_class: string
  - insurance_coverage: string
  - incoterms: string
```

### Data Quality Requirements

| Requirement | Standard |
|-------------|----------|
| Completeness | 90%+ of required fields |
| Accuracy | Verified against source systems |
| Timeliness | Monthly or quarterly updates |
| Format | CSV, JSON, or API push |
| Encryption | AES-256 at rest, TLS 1.3 in transit |

---

## DATA TERMS

### Ownership

- Partner retains full ownership of raw data
- RISKCAST owns derived models and aggregated insights
- Joint ownership of partner-specific calibrations

### Usage Rights

**RISKCAST May**:
- Use data for model training and calibration
- Include in aggregate industry benchmarks (anonymized)
- Derive features and patterns for general model improvement

**RISKCAST May NOT**:
- Share raw data with third parties
- Identify partner in benchmarks without approval
- Use data for purposes other than RISKCAST platform

**Partner May**:
- Use RISKCAST-generated insights internally
- Reference partnership in marketing (with approval)
- Access aggregated benchmarks from other partners

### Exclusivity

- Non-exclusive partnership (default)
- Exclusive arrangements available for Tier 1 partners
- No sharing with direct competitors (defined in agreement)

---

## PRIVACY & SECURITY

### Compliance Framework

| Regulation | Compliance |
|------------|------------|
| GDPR | Full compliance (EU data) |
| CCPA | Full compliance (CA data) |
| SOC 2 Type II | Certification in progress |
| ISO 27001 | Target 2026 |

### Security Controls

1. **Data Encryption**
   - AES-256 at rest
   - TLS 1.3 in transit
   - Key management via HSM

2. **Access Control**
   - Role-based access (RBAC)
   - Multi-factor authentication
   - Audit logging of all access

3. **Data Isolation**
   - Partner data logically separated
   - No cross-partner data visibility
   - Secure deletion upon termination

### Audit Rights

Partner may conduct annual security audit with:
- 30 days written notice
- Reasonable scope agreed in advance
- Results confidential between parties

---

## LEGAL FRAMEWORK

### Term & Termination

| Clause | Terms |
|--------|-------|
| Initial Term | 3 years |
| Renewal | Auto-renew unless 90-day notice |
| Termination for Cause | 30-day cure period |
| Data Return/Deletion | Within 30 days of termination |

### Confidentiality

- Mutual NDA covering all partnership information
- Confidentiality survives termination (3 years)
- Carve-outs for aggregated/anonymized data

### Indemnification

- Mutual indemnification for respective obligations
- Data breach notification within 72 hours
- Cooperation in breach investigation

### Liability

- Liability capped at 12 months of fees/value exchanged
- No consequential damages (mutual)
- Carve-out for gross negligence/willful misconduct

---

## IMPLEMENTATION

### Onboarding Process

```mermaid
graph LR
    A[Agreement Signed] --> B[Data Mapping]
    B --> C[Test Data Transfer]
    C --> D[Quality Validation]
    D --> E[Full Data Integration]
    E --> F[Calibration Complete]
    F --> G[Partner Go-Live]
```

### Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Legal Review | 2-4 weeks | Contract negotiation |
| Data Mapping | 1-2 weeks | Schema alignment, field mapping |
| Test Transfer | 1 week | Sample data, validation |
| Full Integration | 2-4 weeks | Complete data transfer |
| Calibration | 2-4 weeks | Model training, validation |
| Go-Live | 1 week | Partner access, training |

### Success Metrics

| Metric | Target |
|--------|--------|
| Data Quality Score | >90% |
| Calibration Improvement | >15% accuracy gain |
| Partner Satisfaction | >8/10 NPS |
| Renewal Rate | >90% |

---

## CONTACTS

### RISKCAST Partnership Team

| Role | Contact |
|------|---------|
| Partnership Lead | partnerships@riskcast.io |
| Technical Integration | integration@riskcast.io |
| Legal | legal@riskcast.io |
| Data Security | security@riskcast.io |

---

## APPENDICES

### Appendix A: Data Processing Agreement (DPA)
[Separate document]

### Appendix B: Technical Integration Guide
[Separate document]

### Appendix C: Sample NDA
[Separate document]

### Appendix D: Data Quality Checklist
[Separate document]

---

*Template Version: 1.0 | Last Updated: January 2026*
*This template is for discussion purposes. Final agreement subject to legal review.*
