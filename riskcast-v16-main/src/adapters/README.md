# Risk Engine v2 Result Adapter

## Overview

This adapter implements the **ENGINE-FIRST** architecture pattern for the Results page data layer. It normalizes raw engine output (`complete_result` from `GET /results/data`) into a stable, type-safe `ResultsViewModel` that the UI can consume safely.

## Architecture Principles

1. **Frontend NEVER reads raw engine fields directly** - All data must pass through `adaptResultV2()`
2. **Deterministic normalization** - Same input always produces same output
3. **Safe defaults** - Never throws; always returns valid `ResultsViewModel`
4. **Explicit precedence** - Documented rules for handling redundant fields
5. **Warning tracking** - Issues are logged in `meta.warnings` for debugging

## Files

### Types
- `src/types/engine.ts` - `EngineCompleteResultV2` (partial/loose typing for raw engine output)
- `src/types/resultsViewModel.ts` - `ResultsViewModel` (canonical UI model)

### Adapter
- `src/adapters/adaptResultV2.ts` - Main adapter function with normalization logic

### Utilities
- `src/utils/normalize.ts` - Helper functions for safe type conversion and normalization

### Tests
- `src/adapters/adaptResultV2.test.ts` - Comprehensive unit tests covering all edge cases

### Integration
- `src/pages/ResultsPage.tsx` - Example integration showing proper usage pattern

## Precedence Rules

### Risk Score
1. `profile.score` (highest priority)
2. `risk_score`
3. `overall_risk`
4. `0` (default fallback)

### Risk Level
1. `profile.level`
2. `risk_level`
3. `"Unknown"` (default)

### Confidence
1. `profile.confidence`
2. `confidence`
3. `0` (default)

### Drivers
1. `drivers` array
2. `risk_factors` array
3. `factors` array
4. `[]` (empty array)

## Normalization

### Scales
- **Risk scores**: 0-100 (rounded to 1 decimal)
- **Confidence**: 0-100 percentage (rounded to 0 decimals)
- **Driver impact**: 0-100 percentage (rounded to 0 decimals)
- **Profile factors**: 0-100 percentage (rounded to 0 decimals)
- **Layer contribution**: 0-100 percentage (rounded to 0 decimals)

### Auto-detection
- If value > 1 and <= 100: assume already in 0-100 scale
- If value <= 1: assume 0-1 scale and multiply by 100
- All values clamped to [0, 100]

### Dates
- Validated as ISO date strings
- Invalid dates set to `undefined` with warning
- Missing dates handled gracefully

### Timeline
- Projections always sorted: p10 <= p50 <= p90
- Violations automatically repaired with warning
- Empty arrays handled with `hasData: false`

### Scenarios
- Missing IDs generated from title (slugified) or `scenario-<index>`
- All numeric fields default to 0 if missing/invalid

## Usage

```typescript
import { adaptResultV2 } from '@/adapters/adaptResultV2';

// Fetch raw data from backend
const response = await fetch('/results/data');
const rawData: unknown = await response.json();

// CRITICAL: Normalize through adapter
const viewModel = adaptResultV2(rawData);

// Check for warnings (optional, for debugging)
if (viewModel.meta.warnings.length > 0) {
  console.warn('Adapter warnings:', viewModel.meta.warnings);
}

// Use viewModel in UI - NEVER use rawData directly
console.log(viewModel.riskScore.score); // Normalized to 0-100
console.log(viewModel.drivers); // Always an array
```

## Testing

Run tests with:
```bash
npm test adaptResultV2
```

Test coverage includes:
- ✅ Canonical happy path
- ✅ Redundancy handling (precedence rules)
- ✅ Missing arrays and fields
- ✅ Invalid types and coercion
- ✅ Timeline ordering violations
- ✅ Invalid dates
- ✅ Edge cases (null, undefined, non-objects)

## Meta Information

The adapter tracks:
- `meta.warnings`: Array of warning messages for debugging
- `meta.source.canonicalRiskScoreFrom`: Which field was used for risk score
- `meta.source.canonicalDriversFrom`: Which field was used for drivers
- `meta.engineVersion`: Engine version from raw data
- `meta.language`: Language code
- `meta.timestamp`: ISO timestamp (if valid)

## Error Handling

The adapter **never throws** for normal missing data. It always returns a valid `ResultsViewModel` with:
- Sensible defaults (0 for numbers, empty arrays, "Unknown" for levels)
- Warnings in `meta.warnings` for debugging
- Source tracking in `meta.source` for transparency

Only completely invalid input (non-object) triggers a default view model with warnings.

