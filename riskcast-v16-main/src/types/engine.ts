/**
 * Type definitions for Risk Engine v2 output
 * 
 * These types represent the raw engine output structure (complete_result)
 * as returned from GET /results/data endpoint.
 * 
 * Note: These are partial/loose types to handle variations in backend output.
 * The adapter function will normalize these into strict ResultsViewModel types.
 */

/**
 * Raw engine output structure (complete_result from backend)
 * This is a partial type - fields may be missing, null, or have different shapes
 */
export interface EngineCompleteResultV2 {
  // Shipment information
  shipment?: {
    id?: string;
    route?: string;
    pol_code?: string;
    pod_code?: string;
    origin?: string;
    destination?: string;
    mode?: string;
    carrier?: string;
    etd?: string | null;
    eta?: string | null;
    transit_time?: number;
    container?: string;
    cargo?: string;
    incoterm?: string;
    value?: number;
    cargo_value?: number;
  };

  // Risk metrics (may have redundancy)
  risk_score?: number | string | null;
  overall_risk?: number | string | null;
  risk_level?: string | null;
  confidence?: number | string | null;

  // Profile (may contain nested risk_score, risk_level, confidence)
  profile?: {
    score?: number | string | null;
    level?: string | null;
    confidence?: number | string | null;
    explanation?: string[] | null;
    factors?: Record<string, number | string> | null;
    matrix?: {
      probability?: number | string | null;
      severity?: number | string | null;
      quadrant?: string | null;
      description?: string | null;
    } | null;
  } | null;

  // Drivers (may appear as drivers, risk_factors, or factors)
  drivers?: Array<{
    name?: string;
    impact?: number | string;
    description?: string;
    [key: string]: unknown;
  }> | null;
  risk_factors?: Array<{
    name?: string;
    impact?: number | string;
    description?: string;
    [key: string]: unknown;
  }> | null;
  factors?: Array<{
    name?: string;
    impact?: number | string;
    description?: string;
    [key: string]: unknown;
  }> | null;

  // Layers
  layers?: Array<{
    name?: string;
    score?: number | string | null;
    contribution?: number | string | null;
    [key: string]: unknown;
  }> | null;

  // Recommendations
  recommendations?: {
    insurance?: {
      required?: boolean;
      level?: string;
      threshold?: number;
      premium?: number;
    };
    providers?: unknown[];
    timing?: unknown;
    actions?: string[];
    trace?: unknown;
  } | string[] | null;

  // Decision summary
  decision_summary?: {
    confidence?: number | string | null;
    overall_risk?: {
      score?: number | string | null;
      level?: string | null;
    } | null;
    insurance?: {
      status?: string;
      recommendation?: string;
      rationale?: string;
      risk_delta_points?: number | string | null;
      cost_impact_usd?: number | string | null;
      providers?: unknown[];
    } | null;
    timing?: {
      status?: string;
      recommendation?: string;
      rationale?: string;
      optimal_window?: {
        start?: string;
        end?: string;
      } | null;
      risk_reduction_points?: number | string | null;
      cost_impact_usd?: number | string | null;
    } | null;
    routing?: {
      status?: string;
      recommendation?: string;
      rationale?: string;
      best_alternative?: string | null;
      tradeoff?: string | null;
      risk_reduction_points?: number | string | null;
      cost_impact_usd?: number | string | null;
    } | null;
  } | null;

  // Decision signal (frontend compatibility)
  decisionSignal?: {
    recommendation?: string;
    rationale?: string;
    providers?: unknown[];
  } | null;

  // Timing
  timing?: {
    optimalWindow?: {
      start?: string;
      end?: string;
    } | null;
    riskReduction?: number | string | null;
  } | null;

  // Loss metrics (support multiple naming conventions)
  loss?: {
    // VaR at 95% confidence
    p95?: number | string | null;
    var95?: number | string | null;
    var_95?: number | string | null;
    VaR95?: number | string | null;
    // CVaR at 99% confidence
    p99?: number | string | null;
    cvar99?: number | string | null;
    cvar_99?: number | string | null;
    CVaR99?: number | string | null;
    // Expected loss
    expectedLoss?: number | string | null;
    expected_loss?: number | string | null;
    el?: number | string | null;
    EL?: number | string | null;
    // Tail contribution
    tailContribution?: number | string | null;
    tail_contribution?: number | string | null;
  } | null;

  // Loss distribution data (from Monte Carlo simulation)
  loss_distribution?: number[] | null;
  distribution_shapes?: {
    loss_histogram?: {
      counts?: number[];
      bin_edges?: number[];
      bin_centers?: number[];
    } | null;
  } | null;
  financial_distribution?: {
    distribution?: number[];
    [key: string]: unknown;
  } | null;

  // Risk scenario projections (timeline)
  riskScenarioProjections?: Array<{
    date?: string | null;
    p10?: number | string | null;
    p50?: number | string | null;
    p90?: number | string | null;
    phase?: string | null;
  }> | null;

  // Mitigation scenarios
  scenarios?: Array<{
    id?: string | null;
    title?: string;
    category?: string;
    riskReduction?: number | string | null;
    costImpact?: number | string | null;
    isRecommended?: boolean;
    rank?: number | string | null;
    description?: string;
    [key: string]: unknown;
  }> | null;

  // Traces
  traces?: Record<string, {
    layerName?: string;
    steps?: unknown[];
    sensitivity?: Array<{
      name?: string;
      impact?: number | string;
    }>;
  }> | null;

  // Data reliability
  dataReliability?: Array<{
    domain?: string;
    confidence?: number | string | null;
    completeness?: number | string | null;
    freshness?: number | string | null;
    notes?: string;
  }> | null;

  // Metadata
  engine_version?: string;
  language?: string;
  timestamp?: string;

  // Additional fields (allow for engine expansion)
  [key: string]: unknown;
}

