/**
 * ============================================================================
 * RESULTS VIEW MODEL - THE ONLY UI CONTRACT FOR RESULTS PAGE
 * ============================================================================
 * 
 * ⚠️ CRITICAL ARCHITECTURAL CONTRACT ⚠️
 * 
 * This file defines ResultsViewModel as the SINGLE SOURCE OF TRUTH for all
 * Results page UI components. This contract MUST be strictly enforced.
 * 
 * ============================================================================
 * MANDATORY RULES (NON-NEGOTIABLE):
 * ============================================================================
 * 
 * 1. UI MUST NEVER READ RAW ENGINE RESULT
 *    - All Results page components MUST consume ONLY ResultsViewModel
 *    - Direct access to raw engine output (EngineCompleteResultV2) is FORBIDDEN
 *    - Raw engine data structure is an implementation detail and MUST be hidden
 * 
 * 2. ENGINE VERSION CHANGES MUST BE HANDLED VIA ADAPTERS ONLY
 *    - When engine output structure changes, ONLY update adaptResultV2() adapter
 *    - ResultsViewModel contract remains stable across engine versions
 *    - UI components are protected from engine changes by the adapter layer
 *    - Breaking changes in engine output DO NOT break UI components
 * 
 * 3. ALL DATA NORMALIZATION HAPPENS IN ADAPTER LAYER
 *    - adaptResultV2() is responsible for all type coercion, scaling, defaults
 *    - UI components receive pre-normalized, type-safe data
 *    - No business logic or data transformation in UI components
 * 
 * 4. THIS CONTRACT IS IMMUTABLE FOR UI LAYER
 *    - ResultsViewModel fields and structure are stable
 *    - Changes to this contract require coordinated updates across all UI
 *    - Version this contract if breaking changes are absolutely necessary
 * 
 * ============================================================================
 * ARCHITECTURE PATTERN: ENGINE-FIRST
 * ============================================================================
 * 
 * Data Flow:
 *   Engine Output (v2, v3, ...) 
 *     → adaptResultV2() [Adapter Layer]
 *     → ResultsViewModel [UI Contract]
 *     → UI Components [Presentation Layer]
 * 
 * Benefits:
 *   - UI is decoupled from engine implementation
 *   - Engine can evolve without breaking UI
 *   - Type safety enforced at compile time
 *   - Single source of truth for UI data structure
 * 
 * ============================================================================
 * USAGE PATTERN (REQUIRED):
 * ============================================================================
 * 
 * ```typescript
 * // ✅ CORRECT: Use adapter to normalize
 * const rawResult = await fetch('/results/data').then(r => r.json());
 * const viewModel = adaptResultV2(rawResult);
 * // Use viewModel in UI - NEVER use rawResult
 * 
 * // ❌ FORBIDDEN: Direct access to raw engine data
 * const rawResult = await fetch('/results/data').then(r => r.json());
 * // Using rawResult.risk_score directly in UI - VIOLATION!
 * ```
 * 
 * ============================================================================
 * ENFORCEMENT:
 * ============================================================================
 * 
 * - TypeScript types enforce this contract at compile time
 * - Code reviews MUST verify no raw engine data access in UI
 * - Linting rules should flag direct EngineCompleteResultV2 usage in UI files
 * - Tests verify adapter produces valid ResultsViewModel
 * 
 * ============================================================================
 */

/**
 * ResultsViewModel - Canonical UI model for Results page
 * 
 * This is the ONLY type that the Results page UI should consume.
 * All raw engine data must be normalized through adaptResultV2() before use.
 * 
 * ENGINE-FIRST ARCHITECTURE:
 * - UI NEVER reads raw engine fields directly
 * - All values are normalized to consistent scales (0-100 for percentages)
 * - Missing data is handled with sensible defaults
 * - Warnings are tracked in meta.warnings for debugging
 */

/**
 * Risk level classification
 */
export type RiskLevel = 'Low' | 'Medium' | 'High' | 'Critical' | 'Unknown';

/**
 * Shipment information (normalized)
 */
export interface ShipmentViewModel {
  id: string;
  route: string;
  pol: string;
  pod: string;
  carrier: string;
  etd: string | undefined; // ISO date string or undefined if invalid
  eta: string | undefined; // ISO date string or undefined if invalid
  transitTime: number; // days
  container: string;
  cargo: string;
  incoterm: string;
  cargoValue: number; // USD
}

/**
 * Risk score data (normalized to 0-100)
 */
export interface RiskScoreViewModel {
  score: number; // 0-100, rounded to 1 decimal
  level: RiskLevel;
  confidence: number; // 0-100 (percentage), rounded to 0 decimals
}

/**
 * Risk profile matrix
 */
export interface RiskMatrixViewModel {
  probability: number; // 1-9
  severity: number; // 1-9
  quadrant: string;
  description: string;
}

/**
 * Risk profile with factors
 */
export interface RiskProfileViewModel {
  score: number; // 0-100
  level: RiskLevel;
  confidence: number; // 0-100
  explanation: string[];
  factors: Record<string, number>; // All values normalized to 0-100
  matrix: RiskMatrixViewModel;
}

/**
 * Risk driver (normalized)
 */
export interface RiskDriverViewModel {
  name: string;
  impact: number; // 0-100 (percentage)
  description: string;
}

/**
 * Risk layer (normalized)
 */
export interface RiskLayerViewModel {
  name: string;
  score: number; // 0-100
  contribution: number; // 0-100 (percentage)
  category?: string; // TRANSPORT, CARGO, COMMERCIAL, COMPLIANCE, EXTERNAL
  enabled?: boolean;
}

/**
 * Timeline projection point
 */
export interface TimelineProjectionViewModel {
  date: string; // ISO date string
  p10: number; // 0-100
  p50: number; // 0-100
  p90: number; // 0-100
  phase: string;
}

/**
 * Timeline data
 */
export interface TimelineViewModel {
  projections: TimelineProjectionViewModel[];
  hasData: boolean;
}

/**
 * Loss metrics
 */
export interface LossViewModel {
  p95: number; // USD
  p99: number; // USD
  expectedLoss: number; // USD
  tailContribution: number; // percentage (0-100)
}

/**
 * Mitigation scenario
 */
export interface ScenarioViewModel {
  id: string; // Always present (generated if missing)
  title: string;
  category: string;
  riskReduction: number; // points (can be negative)
  costImpact: number; // USD (can be negative for savings)
  isRecommended: boolean;
  rank: number;
  description: string;
}

/**
 * Insurance decision
 */
export interface InsuranceDecisionViewModel {
  status: 'RECOMMENDED' | 'OPTIONAL' | 'NOT_NEEDED' | 'UNKNOWN';
  recommendation: 'BUY' | 'CONSIDER' | 'SKIP' | 'N/A';
  rationale: string;
  riskDeltaPoints: number | null;
  costImpactUsd: number | null;
  providers: unknown[];
}

/**
 * Timing decision
 */
export interface TimingDecisionViewModel {
  status: 'RECOMMENDED' | 'OPTIONAL' | 'NOT_NEEDED' | 'UNKNOWN';
  recommendation: 'ADJUST_ETD' | 'KEEP_ETD' | 'N/A';
  rationale: string;
  optimalWindow: {
    start: string; // ISO date
    end: string; // ISO date
  } | null;
  riskReductionPoints: number | null;
  costImpactUsd: number | null;
}

/**
 * Routing decision
 */
export interface RoutingDecisionViewModel {
  status: 'RECOMMENDED' | 'OPTIONAL' | 'NOT_NEEDED' | 'UNKNOWN';
  recommendation: 'CHANGE_ROUTE' | 'KEEP_ROUTE' | 'N/A';
  rationale: string;
  bestAlternative: string | null;
  tradeoff: string | null;
  riskReductionPoints: number | null;
  costImpactUsd: number | null;
}

/**
 * Decisions summary
 */
export interface DecisionsViewModel {
  insurance: InsuranceDecisionViewModel;
  timing: TimingDecisionViewModel;
  routing: RoutingDecisionViewModel;
}

/**
 * Metadata about data sources and warnings
 */
export interface ResultsMetaViewModel {
  warnings: string[];
  source: {
    canonicalRiskScoreFrom: string; // Which field was used: 'profile.score' | 'risk_score' | 'overall_risk' | 'default'
    canonicalDriversFrom: string; // Which field was used: 'drivers' | 'risk_factors' | 'factors' | 'empty'
  };
  engineVersion: string;
  language: string;
  timestamp: string | undefined;
}

/**
 * Overview slice - contains shipment, risk score, profile, and reasoning
 */
export interface OverviewViewModel {
  shipment: ShipmentViewModel;
  riskScore: RiskScoreViewModel;
  profile: RiskProfileViewModel;
  reasoning: {
    explanation: string; // Engine-generated explanation (STEP 7B.2)
  };
}

/**
 * Breakdown slice - contains layers and factors
 */
export interface BreakdownViewModel {
  layers: RiskLayerViewModel[];
  factors: Record<string, number>; // From profile.factors
}

/**
 * Complete Results View Model
 * 
 * This is the canonical type that Results page UI must consume.
 * All fields are normalized, validated, and have sensible defaults.
 * 
 * STRUCTURE: Slice-based architecture
 * - overview: Shipment, risk score, profile
 * - breakdown: Layers and factors
 * - timeline: Timeline projections
 * - decisions: Insurance, timing, routing decisions
 * - loss: Financial loss metrics
 * - scenarios: Mitigation scenarios
 * - drivers: Risk drivers
 * - meta: Metadata and warnings
 */
export interface ResultsViewModel {
  overview: OverviewViewModel;
  breakdown: BreakdownViewModel;
  timeline: TimelineViewModel;
  decisions: DecisionsViewModel;
  loss: LossViewModel | null;
  scenarios: ScenarioViewModel[];
  drivers: RiskDriverViewModel[];
  meta: ResultsMetaViewModel;
}

