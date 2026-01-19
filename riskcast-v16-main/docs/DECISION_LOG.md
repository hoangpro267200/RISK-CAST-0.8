# RISKCAST Decision Log

This document records architectural decisions made during the enterprise upgrade.

**Format:** Each decision includes context, decision, consequences, and alternatives considered.

---

## DEC-001: Canonical Engine Interface

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 1

### Context
Multiple engine versions (v14, v15, v16, v2) coexisted with different interfaces, making it difficult to maintain and extend.

### Decision
Create a canonical engine interface (`app/core/engine/interface.py`) with standardized dataclasses:
- `RiskRequest` - Standardized input format
- `RiskResult` - Standardized output format
- `RiskEngineInterface` - Base interface contract

### Consequences
**Positive:**
- Single source of truth for engine contract
- Easier to test and maintain
- Clear migration path for legacy engines

**Negative:**
- Requires adapters for backward compatibility
- Initial implementation overhead

### Alternatives Considered
1. **Keep multiple interfaces** - Rejected: Too complex, hard to maintain
2. **Migrate all at once** - Rejected: Too risky, breaks existing functionality
3. **Canonical interface with adapters** - ✅ Chosen: Best balance of consistency and compatibility

---

## DEC-002: Standard Response Envelope

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 2

### Context
API responses had inconsistent formats, making it difficult for clients to handle errors and extract data.

### Decision
Implement standard response envelope:
```json
{
  "success": bool,
  "data": ...,
  "error": { "code": str, "message": str, "details": any } | null,
  "meta": { "request_id": str, "ts": iso, "version": "v16" }
}
```

### Consequences
**Positive:**
- Consistent API responses
- Better error handling
- Request tracing via request_id
- Backward compatible (old fields preserved temporarily)

**Negative:**
- All endpoints need updating (gradual)
- Slightly larger response size

### Alternatives Considered
1. **Keep existing formats** - Rejected: Inconsistent, hard to maintain
2. **Versioned APIs** - Considered: More complex, not needed yet
3. **Standard envelope with backward compat** - ✅ Chosen: Best balance

---

## DEC-003: Frontend Stack: React + TypeScript

**Date:** 2024  
**Status:** ✅ Documented  
**Phase:** Phase 7

### Context
Frontend uses three different stacks: React (Results page), Vue (risk-intelligence), and Vanilla JS (input/summary pages). This fragmentation makes maintenance difficult.

### Decision
**React + TypeScript** is the canonical frontend stack for all new development.

### Consequences
**Positive:**
- Consistency across new features
- Type safety with TypeScript
- Modern tooling (Vite, React SWC)
- Better developer experience

**Negative:**
- Legacy code (Vue, Vanilla JS) still needs maintenance
- Gradual migration required

### Alternatives Considered
1. **Keep all three stacks** - Rejected: Too fragmented, hard to maintain
2. **Migrate everything to React** - Rejected: Too risky, big-bang migration
3. **Choose React for new code, maintain legacy** - ✅ Chosen: Best balance

---

## DEC-004: Caching Strategy

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 5

### Context
Risk calculations are expensive (Monte Carlo 50k iterations). Repeated requests with same inputs should be cached.

### Decision
Implement caching with:
- In-memory cache (default)
- Optional Redis backend
- Cache key from normalized RiskRequest (MD5 hash)
- Configurable TTL (default 1 hour)

### Consequences
**Positive:**
- Reduced latency for repeated requests
- Lower server load
- Same inputs return cached results

**Negative:**
- Memory usage (in-memory cache)
- Cache invalidation complexity
- Potential stale data (mitigated by TTL)

### Alternatives Considered
1. **No caching** - Rejected: Performance issues
2. **Redis only** - Rejected: Adds dependency, in-memory simpler
3. **In-memory with Redis option** - ✅ Chosen: Best balance

---

## DEC-005: State Storage: File-based with MySQL Option

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 6

### Context
Shipment state is only in localStorage, causing data loss on cache clear. Need backend persistence.

### Decision
Implement state storage with:
- File-based storage (default) - `data/state/{shipment_id}.json`
- Optional MySQL backend (if `USE_MYSQL=true`)
- Conflict resolution: last-write-wins with `updated_at`

### Consequences
**Positive:**
- Data persistence
- No database required (file-based works out of box)
- Optional MySQL for scalability

**Negative:**
- File-based: Not suitable for high concurrency
- MySQL: Adds dependency

### Alternatives Considered
1. **MySQL only** - Rejected: Adds dependency, not always needed
2. **File-based only** - Rejected: Doesn't scale
3. **File-based with MySQL option** - ✅ Chosen: Best balance

---

## DEC-006: Fast Mode for Development

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 5

### Context
Monte Carlo with 50k iterations is slow for development. Need faster iteration.

### Decision
Implement fast mode:
- Development: `MC_ITERATIONS_DEV=5000` (10x faster)
- Production: `MC_ITERATIONS=50000` (default)
- Auto-detected from `ENVIRONMENT` variable

### Consequences
**Positive:**
- Faster development cycles
- Same code path (just different iterations)
- Configurable per environment

**Negative:**
- Lower accuracy in dev (acceptable trade-off)
- Need to remember to test with production iterations

### Alternatives Considered
1. **Fixed iterations** - Rejected: Too slow for dev
2. **Separate dev engine** - Rejected: Code duplication
3. **Configurable iterations** - ✅ Chosen: Best balance

---

## DEC-007: Request ID Propagation

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 2

### Context
Need request tracing across services for debugging and monitoring.

### Decision
Implement request ID middleware:
- Generate unique UUID per request
- Store in `request.state.request_id`
- Include in response headers (`X-Request-ID`)
- Include in response meta
- Include in logs

### Consequences
**Positive:**
- Request tracing
- Better debugging
- Correlation across services

**Negative:**
- Slight overhead (minimal)
- Need to propagate in all handlers

### Alternatives Considered
1. **No request ID** - Rejected: Hard to debug
2. **External tracing (e.g., OpenTelemetry)** - Considered: Overkill for now
3. **Simple request ID middleware** - ✅ Chosen: Simple and effective

---

## DEC-008: Legacy Code Archive Strategy

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 1

### Context
Legacy code (v14, v15, old pages) mixed with active code, making it hard to understand what's current.

### Decision
Create `archive/` folder:
- Move legacy code to archive (not delete)
- Keep imports working via adapters
- Document deprecation timeline

### Consequences
**Positive:**
- Clear separation of active vs. legacy
- History preserved
- No breaking changes

**Negative:**
- Code still in repo (larger size)
- Need adapters for backward compat

### Alternatives Considered
1. **Delete legacy code** - Rejected: Too risky, breaks compatibility
2. **Keep in place** - Rejected: Too confusing
3. **Archive with adapters** - ✅ Chosen: Best balance

---

## DEC-009: Security: Production CORS Enforcement

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 4

### Context
CORS configuration had defaults that could be insecure in production.

### Decision
Enforce explicit `ALLOWED_ORIGINS` in production:
- Production: Raises error if `ALLOWED_ORIGINS` not set
- Development: Defaults to localhost origins
- Never allow wildcard `*` in production

### Consequences
**Positive:**
- Prevents accidental insecure deployment
- Clear security requirements

**Negative:**
- Deployment requires explicit configuration
- Slight friction (acceptable for security)

### Alternatives Considered
1. **Keep defaults** - Rejected: Security risk
2. **Warn only** - Rejected: Too easy to ignore
3. **Enforce in production** - ✅ Chosen: Best security

---

## DEC-010: Testing: Engine Invariants

**Date:** 2024  
**Status:** ✅ Implemented  
**Phase:** Phase 3

### Context
Engine refactoring needs protection. Need tests that verify core invariants.

### Decision
Create engine invariant tests:
- Risk score bounds [0, 10]
- Monotonicity (worse inputs don't reduce risk)
- Layer results structure
- Confidence bounds
- Financial metrics validity

### Consequences
**Positive:**
- Protects against regressions
- Validates engine correctness
- Enables confident refactoring

**Negative:**
- Test maintenance overhead
- Some tests may be slow (MC tests)

### Alternatives Considered
1. **No invariant tests** - Rejected: Too risky
2. **Only integration tests** - Rejected: Don't catch all issues
3. **Invariant + integration tests** - ✅ Chosen: Best coverage

---

## Decision Template

When making new architectural decisions, use this template:

```markdown
## DEC-XXX: Decision Title

**Date:** YYYY-MM-DD
**Status:** Proposed/Implemented/Rejected
**Phase:** Phase X

### Context
[Why this decision is needed]

### Decision
[What was decided]

### Consequences
**Positive:**
- [Benefit 1]
- [Benefit 2]

**Negative:**
- [Drawback 1]
- [Drawback 2]

### Alternatives Considered
1. **Alternative 1** - Rejected: [Reason]
2. **Alternative 2** - Considered: [Reason]
3. **Chosen alternative** - ✅ Chosen: [Reason]
```

---

**Last Updated:** 2024  
**Maintained By:** RISKCAST Engineering Team

