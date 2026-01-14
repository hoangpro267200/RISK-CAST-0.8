# RISKCAST Trade Secret Inventory

## Classification: STRICTLY CONFIDENTIAL

**Access Control**: Need-to-know basis only. Access requires signed NDA and management approval.

---

## Overview

This document inventories trade secrets that provide competitive advantage and should NOT be disclosed through patents, publications, or open-source releases.

---

## Trade Secret Register

### TS-001: Calibration Coefficients

**Classification**: CRITICAL

**Description**: Exact calibration parameters derived from historical data analysis.

| Parameter | Description | Why Secret |
|-----------|-------------|------------|
| Platt scaling A/B | Logistic regression coefficients | Hard to replicate without data |
| Isotonic breakpoints | Non-parametric calibration curve | Result of extensive calibration |
| Bayesian priors | Prior distributions for risk factors | Domain expertise encoded |

**Protection Measures**:
- Stored in encrypted configuration files
- Access logged and audited
- Parameters obfuscated in deployed code
- No comments explaining derivation

**Authorized Access**:
- Data Science Lead
- CTO
- Calibration Engineer (read-only)

---

### TS-002: FAHP Weight Optimization

**Classification**: HIGH

**Description**: Optimized pairwise comparison weights for the FAHP algorithm.

| Component | Description | Why Secret |
|-----------|-------------|------------|
| Base weights | Initial weight matrix | Expert judgment encoded |
| Calibration adjustments | Domain-specific modifications | Industry expertise |
| Regional factors | Geographic weight modifiers | Proprietary data sources |
| Temporal adjustments | Seasonal weight variations | Historical analysis |

**Protection Measures**:
- Weights stored separately from main codebase
- Runtime injection only
- No weight values in source code comments
- Encrypted at rest

**Authorized Access**:
- Risk Model Team
- Data Science Lead

---

### TS-003: Fraud Detection Rules

**Classification**: HIGH

**Description**: Specific thresholds and patterns for detecting gaming attempts.

| Component | Description | Why Secret |
|-----------|-------------|------------|
| Strategic omission patterns | Fields commonly omitted by bad actors | Would enable evasion |
| Benford's Law thresholds | Deviation thresholds for anomaly detection | Would enable gaming |
| Behavioral fingerprints | User patterns indicating fraud | Proprietary detection |
| Cross-validation rules | Consistency check logic | Bypass prevention |

**Protection Measures**:
- Rules engine separate from main application
- Hot-reloadable without code deployment
- No rule details in logs or errors
- Regular rule updates to prevent adaptation

**Authorized Access**:
- Fraud Detection Team
- Security Lead

---

### TS-004: Historical Training Dataset

**Classification**: CRITICAL

**Description**: Curated historical shipment data with actual outcomes.

| Component | Description | Why Secret |
|-----------|-------------|------------|
| Partner data | Data from partnership agreements | Contractual protection |
| Outcome labels | Delay/loss/incident records | Ground truth for calibration |
| Feature engineering | Derived features from raw data | Proprietary methodology |
| Data cleaning logic | Handling of edge cases | Expert knowledge |

**Protection Measures**:
- Data stored in isolated, encrypted database
- No data exports without executive approval
- Access via secure query interface only
- Aggregated metrics only in reports

**Authorized Access**:
- Data Science Team (via secure interface)
- CTO (for partnership discussions)

---

### TS-005: Monte Carlo Distribution Parameters

**Classification**: MEDIUM

**Description**: Specific distribution parameters for risk factor simulation.

| Component | Description | Why Secret |
|-----------|-------------|------------|
| Distribution selection | Which distribution for each factor | Empirical optimization |
| Shape parameters | Alpha, beta, sigma values | Calibrated to data |
| Correlation matrices | Factor interdependencies | Domain expertise |
| Tail behavior models | Extreme event parameters | Proprietary research |

**Protection Measures**:
- Parameters in encrypted config
- Runtime loading only
- Obfuscated variable names

**Authorized Access**:
- Quantitative Modeling Team

---

### TS-006: Insurance Premium Algorithms

**Classification**: MEDIUM

**Description**: Specific formulas for premium calculation and risk classification.

| Component | Description | Why Secret |
|-----------|-------------|------------|
| Risk class boundaries | Score thresholds for classes | Competitive advantage |
| Multiplier tables | Adjustment factors by category | Actuarial optimization |
| Deductible formulas | Deductible calculation logic | Pricing intelligence |
| Portfolio discount curves | Volume discount structures | Commercial terms |

**Protection Measures**:
- Algorithms separate from public documentation
- No formulas in client-facing materials
- Generic descriptions only in sales materials

**Authorized Access**:
- Insurance Product Team
- Finance Team

---

### TS-007: Carrier Reliability Scoring

**Classification**: MEDIUM

**Description**: Methodology for scoring carrier/forwarder reliability.

| Component | Description | Why Secret |
|-----------|-------------|------------|
| Data sources | Specific data feeds used | Competitive sourcing |
| Scoring formula | Weighted calculation | Proprietary methodology |
| Decay functions | How old data is weighted | Optimization |
| Blacklist criteria | Automatic exclusion rules | Risk management |

**Protection Measures**:
- Carrier scores available, methodology hidden
- No methodology in API documentation
- Vague descriptions in public materials

**Authorized Access**:
- Operations Team
- Partner Management

---

## Protection Protocols

### Employee Onboarding

1. Sign comprehensive NDA before access to any trade secrets
2. Trade secret awareness training within first week
3. Access provisioned on need-to-know basis only
4. Quarterly reminders of obligations

### Access Control

1. Trade secrets stored in separate, encrypted repositories
2. Multi-factor authentication required
3. Access logged with reason required
4. Quarterly access reviews

### Departure Protocol

1. Exit interview includes trade secret reminder
2. All access revoked immediately upon departure notice
3. Written acknowledgment of ongoing obligations
4. Non-compete enforcement if applicable

### Incident Response

1. Suspected disclosure reported immediately to Legal
2. Access suspended pending investigation
3. Legal assessment within 24 hours
4. Enforcement action if warranted

---

## Audit Log

| Date | Action | User | Trade Secret | Justification |
|------|--------|------|--------------|---------------|
| [Date] | Access Granted | [User] | TS-001 | Calibration work |
| [Date] | Access Revoked | [User] | TS-003 | Role change |
| [Date] | Quarterly Review | [Admin] | All | Scheduled audit |

---

## Legal References

- **Defend Trade Secrets Act (DTSA)**: Federal trade secret protection
- **Uniform Trade Secrets Act (UTSA)**: State-level protection
- **Economic Espionage Act**: Criminal penalties for theft

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2026 | [Author] | Initial creation |

---

*This document is a trade secret. Unauthorized disclosure is prohibited.*
