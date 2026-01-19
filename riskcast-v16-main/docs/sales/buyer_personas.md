# RISKCAST Buyer Personas

## Stakeholder Psychology Matrix

Understanding buyer psychology is critical for sales conversion. This document profiles each persona, their decision dynamics, and how to win them over.

---

## 1. ANALYST (Technical Evaluator)

### Profile

| Attribute | Description |
|-----------|-------------|
| **Role** | Risk Analyst, Data Scientist, Operations Analyst |
| **Decision Power** | 25% (recommends but doesn't sign) |
| **Reports To** | Operations Manager, VP Operations, CRO |
| **Daily Pain** | Manual spreadsheets, inconsistent methods, time pressure |

### Psychology

**What They Care About:**
- Technical accuracy and methodology soundness
- Reproducibility and explainability
- Integration with existing tools
- Not looking stupid in front of leadership

**What They Fear:**
- Recommending a tool that fails
- Being automated out of a job
- Learning curve / complexity
- Black box they can't explain

**Decision Criteria:**
1. Does the methodology make sense? (FAHP, TOPSIS, Monte Carlo)
2. Can I verify the accuracy myself?
3. Will this make my job easier or harder?
4. Can I explain it to my boss?

### How to Win Them

**Approach:**
- Lead with methodology (white paper, sensitivity analysis)
- Offer sandbox access for testing
- Show how it augments (not replaces) their expertise
- Provide technical deep-dive session

**Key Messages:**
- "Built on peer-reviewed MCDM methods - not a black box"
- "You can export every calculation for audit"
- "87% accuracy on 2,000 historical shipments"
- "30 seconds vs 4 hours - more time for high-value analysis"

**Red Flags:**
- Asks only about price (not technical fit)
- Won't engage with demo
- "I need to run this by IT" (may be a blocker)

**Success Signal:**
- Requests API documentation
- Asks to test with their own data
- Introduces you to their manager

---

## 2. EXECUTIVE (Economic Buyer)

### Profile

| Attribute | Description |
|-----------|-------------|
| **Role** | CFO, COO, VP Operations, VP Supply Chain |
| **Decision Power** | 40% (ultimate budget authority) |
| **Reports To** | CEO, Board |
| **Daily Pain** | Cost overruns, surprise delays, insurance claims |

### Psychology

**What They Care About:**
- ROI and cost justification
- Strategic alignment
- Risk mitigation for the company
- Looking good to the board

**What They Fear:**
- Spending money on tools that don't deliver
- Being blamed for delays/losses
- Vendor lock-in
- Implementation failure

**Decision Criteria:**
1. What's the ROI? (Must be >3x)
2. What's the payback period? (Must be <12 months)
3. Does this align with our strategy?
4. What's the risk of NOT doing this?

### How to Win Them

**Approach:**
- Lead with business outcomes, not features
- Provide custom ROI analysis with their numbers
- Offer reference calls with peer executives
- Quantify cost of inaction

**Key Messages:**
- "30% reduction in delay-related costs"
- "$250k+ annual savings (typical customer)"
- "Payback in 3-4 months"
- "One prevented incident pays for 3 years of RISKCAST"

**Red Flags:**
- "Send me the materials and I'll review" (no meeting)
- Delegates everything to procurement
- "We're not prioritizing this right now"

**Success Signal:**
- Asks about implementation timeline
- Wants to talk to existing customers
- Asks about contract terms

---

## 3. PROCUREMENT (Process Gatekeeper)

### Profile

| Attribute | Description |
|-----------|-------------|
| **Role** | Procurement Manager, Vendor Manager, Sourcing Specialist |
| **Decision Power** | 15% (influences, enforces compliance) |
| **Reports To** | CFO, CPO |
| **Daily Pain** | Vendor compliance, contract negotiations, risk management |

### Psychology

**What They Care About:**
- Process compliance
- Competitive pricing
- Contract terms (liability, SLA, exit)
- Vendor stability

**What They Fear:**
- Selecting a vendor that fails
- Audit findings
- Non-compliant purchases
- Being bypassed by business users

**Decision Criteria:**
1. Are you on our approved vendor list?
2. Do you meet security requirements?
3. Is pricing competitive?
4. What are the contract terms?

### How to Win Them

**Approach:**
- Provide complete vendor qualification package upfront
- Be transparent about pricing
- Offer flexible contract terms
- Make their job easy (pre-filled forms)

**Key Messages:**
- "Here's our complete security documentation"
- "SOC 2 Type II in progress (Q2 2026)"
- "Standard MSA with customer-friendly terms"
- "We support your RFP process"

**Red Flags:**
- Requesting aggressive discounts without commitment
- Endless documentation requests (stalling)
- "We're just gathering information"

**Success Signal:**
- Starts vendor qualification process
- Sends MSA for legal review
- Asks about implementation timeline

---

## 4. INSURANCE UNDERWRITER (Domain Expert)

### Profile

| Attribute | Description |
|-----------|-------------|
| **Role** | Underwriting Manager, Chief Underwriting Officer, Actuary |
| **Decision Power** | 20% (veto power if methodology flawed) |
| **Reports To** | CEO, Board |
| **Daily Pain** | Manual underwriting, pricing accuracy, loss ratios |

### Psychology

**What They Care About:**
- Actuarial soundness
- Regulatory compliance (Solvency II, ASOP)
- Combined ratio improvement
- Model explainability for auditors

**What They Fear:**
- Underwriting bad risk
- Regulatory findings
- Model failure at scale
- Losing job over model error

**Decision Criteria:**
1. Is this actuarially sound?
2. Can we use this for underwriting (or just advisory)?
3. What's the validation track record?
4. How does it handle edge cases?

### How to Win Them

**Approach:**
- Lead with calibration metrics (Brier, ECE, MAE)
- Acknowledge regulatory path clearly
- Position as decision support, not replacement
- Offer shadow underwriting pilot

**Key Messages:**
- "Brier score 0.12, ECE 0.04 - actuarially acceptable"
- "Human-in-the-loop - underwriters retain final authority"
- "Actuarial certification roadmap: Q3 2026"
- "87% accuracy identifying high-risk shipments"

**Red Flags:**
- "We can't use any external models"
- Legal/compliance blocks all new vendors
- No budget allocated for underwriting tech

**Success Signal:**
- Requests methodology white paper
- Introduces you to their actuary
- Asks about shadow underwriting pilot

---

## 5. END USER (Champion or Blocker)

### Profile

| Attribute | Description |
|-----------|-------------|
| **Role** | Operations Manager, Logistics Coordinator, Risk Coordinator |
| **Decision Power** | 10% (can sabotage adoption) |
| **Reports To** | VP Operations |
| **Daily Pain** | Manual processes, fire-fighting, customer complaints |

### Psychology

**What They Care About:**
- Ease of use
- Time savings
- Not adding to their workload
- Looking competent to their boss

**What They Fear:**
- Complex new systems
- Being blamed when tool fails
- Job displacement
- Learning curve

**Decision Criteria:**
1. Will this make my job easier?
2. How long until I'm productive?
3. What if it gives wrong answers?
4. Will my boss know if I don't use it?

### How to Win Them

**Approach:**
- Demo the simple mode (5 fields, 30 seconds)
- Emphasize time savings, not methodology
- Offer hands-on training
- Address job security concerns

**Key Messages:**
- "5 fields, one click, 30 seconds"
- "Your expertise + RISKCAST = superhuman"
- "We train your whole team in 30 minutes"
- "Most teams are productive in 3 days"

**Red Flags:**
- "We tried something like this before and it failed"
- Silent in meetings (passive resistance)
- "I don't have time to learn new tools"

**Success Signal:**
- Actively participates in demo
- Asks about specific use cases
- Volunteers to be pilot user

---

## 6. VC INVESTOR (Capital Provider)

### Profile

| Attribute | Description |
|-----------|-------------|
| **Role** | Partner, Principal at VC firm |
| **Decision Power** | 100% (for funding decision) |
| **Reports To** | LP Committee |
| **Daily Pain** | Finding breakout companies, portfolio performance |

### Psychology

**What They Care About:**
- Market size (TAM/SAM/SOM)
- Defensibility / moat
- Team quality
- Traction / momentum

**What They Fear:**
- Investing in a feature, not a company
- Market too small
- Founder/market fit
- Being wrong (reputation)

**Decision Criteria:**
1. Is the market big enough? ($100M+ TAM)
2. Can this be a $1B company?
3. Is there a defensible moat?
4. Does the team have unfair advantages?

### How to Win Them

**Approach:**
- Lead with market opportunity
- Show traction before asking for money
- Demonstrate domain expertise
- Have clear path to $100M ARR

**Key Messages:**
- "$280M-500M TAM with expansion paths"
- "Only calibrated logistics risk engine (no competition)"
- "Data network effects as moat"
- "$120k ARR, 50 pilots, 3 insurance partnerships"

**Red Flags:**
- "This seems like a feature of Flexport"
- No follow-up meeting scheduled
- "We're not actively investing in logistics"

**Success Signal:**
- Requests follow-up with partner
- Asks for customer introductions
- Wants to see data room

---

## 7. ACADEMIC JUDGE (Competition Evaluator)

### Profile

| Attribute | Description |
|-----------|-------------|
| **Role** | Professor, Researcher, Industry Expert |
| **Decision Power** | 100% (for competition) |
| **Reports To** | Competition Committee |
| **Daily Pain** | Reading mediocre submissions |

### Psychology

**What They Care About:**
- Novelty and originality
- Methodological rigor
- Practical applicability
- Clear presentation

**What They Fear:**
- Recommending weak projects
- Plagiarism / ethics issues
- Wasting time on poor submissions

**Decision Criteria:**
1. Is this novel? (Not just combining known methods)
2. Is the methodology sound?
3. Is it validated with real data?
4. Is the presentation clear?

### How to Win Them

**Approach:**
- Lead with novelty statement
- Show literature review and positioning
- Provide validation metrics
- Practice delivery until smooth

**Key Messages:**
- "First integration of FAHP + TOPSIS + calibrated Monte Carlo for logistics"
- "Validated on 2,000 shipments (13x larger than Chen 2019)"
- "Bridges academic MCDM with actuarial standards"
- "87% accuracy, MAE 12.3 points"

**Red Flags:**
- Methodology questions you can't answer
- "Why didn't you use [alternative method]?"
- "Your sample size seems small"

**Success Signal:**
- Nodding during presentation
- Asks about publication plans
- "This is interesting work"

---

## Stakeholder Decision Dynamics

### Power Map

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│     HIGH POWER                                               │
│         ▲                                                    │
│         │     ┌──────────────┐    ┌──────────────┐          │
│         │     │  EXECUTIVE   │    │  UNDERWRITER │          │
│         │     │   (CFO/COO)  │    │   (Veto)     │          │
│         │     └──────────────┘    └──────────────┘          │
│         │                                                    │
│         │     ┌──────────────┐    ┌──────────────┐          │
│         │     │  ANALYST     │    │  PROCUREMENT │          │
│         │     │  (Technical) │    │  (Process)   │          │
│         │     └──────────────┘    └──────────────┘          │
│         │                                                    │
│         │     ┌──────────────┐                               │
│         │     │   END USER   │                               │
│         │     │  (Adoption)  │                               │
│         │     └──────────────┘                               │
│         │                                                    │
│     LOW POWER                                                │
│                                                              │
│    AGAINST ◄──────────────────────────────────────► SUPPORT │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Winning the Deal

1. **Identify the Economic Buyer** (usually Executive)
2. **Win the Technical Evaluator** (Analyst) first
3. **Neutralize Gatekeepers** (Procurement, Underwriter)
4. **Create Champions** (End Users)
5. **Multi-thread** (never rely on single contact)

### Common Failure Modes

| Failure Mode | What Happened | Prevention |
|--------------|---------------|------------|
| Single-threaded | Champion left, deal died | Always have 3+ contacts |
| No executive access | Stuck at analyst level | Ask for intro to decision maker |
| Procurement stall | Endless documentation | Start vendor qualification early |
| End user sabotage | Low adoption → cancellation | Include users in evaluation |
| Budget surprise | "We don't have budget" | Qualify budget in first call |

---

*Document Version: 2.0 | Last Updated: January 2026*
