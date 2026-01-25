# Post-Mortem: [Incident Title]

**Date:** [YYYY-MM-DD]  
**Incident Commander:** [Name]  
**Severity:** SEV-[1/2/3/4]  
**Duration:** [X hours Y minutes]

---

## 📝 Executive Summary

[1-2 sentence summary of what happened and the impact]

**Impact:**
- Users affected: [Number or percentage]
- Requests failed: [Number]
- Revenue impact: [Amount if applicable]
- Duration: [Start time] - [End time]

---

## ⏱️ Timeline

All times in UTC

| Time | Event | Action |
|------|-------|--------|
| HH:MM | [Event] | [Action taken] |
| HH:MM | Incident detected | On-call paged via PagerDuty |
| HH:MM | IC declared, team assembled | Created #incident-YYYYMMDD channel |
| HH:MM | [Investigation finding] | [Action taken] |
| HH:MM | Mitigation implemented | [What was done] |
| HH:MM | Service restored | [Verification] |
| HH:MM | Incident resolved | Monitoring for stability |
| HH:MM | Post-mortem scheduled | [Date/time] |

---

## 🔍 Root Cause Analysis

### What Happened?

[Detailed technical explanation of the root cause]

### Why Did It Happen?

[Underlying reasons, contributing factors, chain of events]

### Why Wasn't It Caught Earlier?

[Why monitoring/testing didn't catch this, what gaps existed]

### Why Didn't Monitoring Alert Sooner?

[Why alerts didn't fire or were insufficient]

---

## 📊 Impact Assessment

### User Impact

- **Total users affected:** [Number]
- **Percentage of user base:** [X%]
- **User experience:** [Description of what users saw]
- **Geographic distribution:** [If relevant]

### Business Impact

- **Requests failed:** [Number]
- **Error rate:** [X%] (baseline: [Y%])
- **Revenue impact:** $[Amount] (estimated)
- **Reputation impact:** [Severity: Low/Medium/High]
- **SLA breach:** [Yes/No - if yes, details]

### Technical Impact

- **Services affected:** [List]
- **Data loss:** [Yes/No - if yes, details]
- **Performance degradation:** [Details]
- **Recovery time:** [Actual vs. RTO]

---

## ✅ What Went Well

[List things that went well during the incident]

**Examples:**
- Fast detection (within X minutes)
- Effective communication (updates every Y minutes)
- Quick mitigation (resolved in Z minutes)
- Good team coordination
- Successful rollback
- No data loss

---

## ❌ What Went Wrong

[List things that didn't go well or could be improved]

**Examples:**
- Slow detection (took X minutes to notice)
- Delayed response (team took Y minutes to assemble)
- Unclear communication
- Missing documentation
- Ineffective first mitigation attempt
- Alerts didn't fire as expected

---

## 🎯 Action Items

### Preventive Measures (P0 - Fix ASAP)

- [ ] **[Action 1]**
  - **Owner:** [Name]
  - **Due:** [Date]
  - **Status:** Not started / In progress / Done
  - **Details:** [What needs to be done]

- [ ] **[Action 2]**
  - **Owner:** [Name]
  - **Due:** [Date]
  - **Status:** Not started / In progress / Done

### Detection Improvements (P1 - High Priority)

- [ ] **Add alert for [condition]**
  - **Owner:** [Name]
  - **Due:** [Date]

- [ ] **Improve monitoring of [metric]**
  - **Owner:** [Name]
  - **Due:** [Date]

### Process Improvements (P2 - Medium Priority)

- [ ] **Update runbook with [new procedure]**
  - **Owner:** [Name]
  - **Due:** [Date]

- [ ] **Improve communication template**
  - **Owner:** [Name]
  - **Due:** [Date]

### Documentation Updates (P3 - Low Priority)

- [ ] **Document [new finding]**
  - **Owner:** [Name]
  - **Due:** [Date]

- [ ] **Update architecture diagram**
  - **Owner:** [Name]
  - **Due:** [Date]

---

## 💡 Lessons Learned

### Technical Lessons

[Technical insights gained from this incident]

**Examples:**
- Database connection pool needs to be larger for peak load
- External API has undocumented rate limits
- Specific query is slow and needs optimization
- Caching strategy was insufficient

### Process Lessons

[Process insights and improvements]

**Examples:**
- Need faster way to reach DBA during incidents
- Communication template should include more details
- Escalation path needs clarification
- Post-mortem should happen sooner

### Team Lessons

[Team dynamics and collaboration insights]

**Examples:**
- Need more training on [topic]
- Documentation needs to be more accessible
- Need better handoff procedures
- On-call rotation needs adjustment

---

## 📚 Supporting Links

- **Incident Channel:** [#incident-YYYYMMDD-description]
- **Jira Ticket:** [INCIDENT-XXX]
- **Status Page:** [Link to incident on status page]
- **Monitoring Dashboard:** [Grafana dashboard link]
- **Related PRs:** [PR #123, PR #456]
- **GitHub Security Advisory:** [If applicable]

---

## 👥 Attendees

**Post-Mortem Meeting:**
- **Date:** [YYYY-MM-DD]
- **Attendees:** [List all attendees]
- **Duration:** 60 minutes

**Required:**
- Incident Commander
- Key responders
- Engineering Manager

**Optional:**
- Support team representatives
- Product managers
- Sales (if customer-facing impact)

---

## 💬 Discussion Notes

[Key points discussed during the post-mortem meeting]

---

## ✅ Follow-Up

- [ ] All action items assigned
- [ ] Due dates set
- [ ] Follow-up meeting scheduled (if needed)
- [ ] Incident documentation archived
- [ ] Lessons shared with broader team
- [ ] Runbooks updated
- [ ] Training conducted (if needed)

---

**Post-Mortem completed:** [Date]  
**Document owner:** [Name]  
**Review date:** [30 days from incident]

---

**REMEMBER:** This is a **BLAMELESS** post-mortem. Focus on systems and processes, not individuals. The goal is to learn and improve, not to assign blame.

**Questions to ask:**
- What can we do to prevent this?
- What can we do to detect it faster?
- What can we do to recover faster?
- What can we do to communicate better?

**NOT:**
- Who is at fault?
- Who made the mistake?
- Who should have caught this?

**Culture:** We assume everyone was doing their best with the information available at the time. We focus on improving systems, not punishing people.

---

**Learning is the goal. Improvement is the outcome.** 🎯
