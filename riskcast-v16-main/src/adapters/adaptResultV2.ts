/**
 * Risk Engine v2 Result Adapter
 * 
 * Converts raw engine output (complete_result) to normalized ResultsViewModel.
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - Frontend MUST NEVER read raw engine fields directly
 * - All data must pass through this adapter
 * - Adapter handles redundancy, missing fields, type coercion, and normalization
 * 
 * PRECEDENCE RULES (documented in code):
 * - riskScore: profile.score > risk_score > overall_risk > 0
 * - riskLevel: profile.level > risk_level > "Unknown"
 * - confidence: profile.confidence > confidence > 0
 * - drivers: drivers > risk_factors > factors > []
 * 
 * NORMALIZATION:
 * - All percentages normalized to 0-100 scale
 * - All numbers rounded appropriately
 * - Dates validated as ISO strings
 * - Missing data handled with sensible defaults
 * - Warnings tracked in meta.warnings
 */

import type { EngineCompleteResultV2 } from '@/types/engine';
import type { ResultsViewModel } from '@/types/resultsViewModel';
import {
  toNumber,
  clamp,
  toPercent,
  round,
  isValidISODate,
  slugify,
  toString,
  toArray,
  normalizeRiskLevel,
} from '@/utils/normalize';

/**
 * Adapt raw engine result to normalized ResultsViewModel
 * 
 * @param raw - Raw engine output (may be unknown type)
 * @returns Normalized ResultsViewModel (never throws, always returns valid model)
 */
export function adaptResultV2(raw: unknown): ResultsViewModel {
  // Type guard: ensure we have an object
  if (typeof raw !== 'object' || raw === null) {
    return createDefaultViewModel(['Invalid input: expected object']);
  }

  const data = raw as EngineCompleteResultV2;
  const warnings: string[] = [];

  // Check if data is effectively empty (no meaningful fields)
  const hasData = 
    (data.risk_score !== undefined && data.risk_score !== null) ||
    (data.profile?.score !== undefined && data.profile?.score !== null) ||
    (data.overall_risk !== undefined && data.overall_risk !== null) ||
    (Object.keys(data).length > 0 && Object.keys(data).some(key => 
      key !== 'timestamp' && key !== 'engine_version' && key !== 'language'
    ));
  
  if (!hasData) {
    warnings.push('Empty or invalid data received from backend');
  }

  // ============================================================
  // RISK SCORE PRECEDENCE: profile.score > risk_score > overall_risk > 0
  // ============================================================
  let canonicalRiskScore = 0;
  let canonicalRiskScoreFrom = 'default';

  const profileScore = data.profile?.score;
  const riskScore = data.risk_score;
  const overallRisk = data.overall_risk;

  if (profileScore !== null && profileScore !== undefined) {
    canonicalRiskScore = toPercent(profileScore);
    canonicalRiskScoreFrom = 'profile.score';
  } else if (riskScore !== null && riskScore !== undefined) {
    canonicalRiskScore = toPercent(riskScore);
    canonicalRiskScoreFrom = 'risk_score';
  } else if (overallRisk !== null && overallRisk !== undefined) {
    canonicalRiskScore = toPercent(overallRisk);
    canonicalRiskScoreFrom = 'overall_risk';
  } else {
    warnings.push('Risk score missing - using default 0');
  }

  // Round to 1 decimal
  canonicalRiskScore = round(canonicalRiskScore, 1);

  // ============================================================
  // RISK LEVEL PRECEDENCE: profile.level > risk_level > "Unknown"
  // ============================================================
  let canonicalRiskLevel = normalizeRiskLevel(
    data.profile?.level ?? data.risk_level ?? 'Unknown'
  );

  // ============================================================
  // CONFIDENCE PRECEDENCE: profile.confidence > confidence > 0
  // ============================================================
  let canonicalConfidence = 0;
  const profileConfidence = data.profile?.confidence;
  const confidence = data.confidence;

  if (profileConfidence !== null && profileConfidence !== undefined) {
    canonicalConfidence = toPercent(profileConfidence);
  } else if (confidence !== null && confidence !== undefined) {
    canonicalConfidence = toPercent(confidence);
  }

  // Round to 0 decimals (percentage)
  canonicalConfidence = Math.round(canonicalConfidence);

  // ============================================================
  // DRIVERS: ENGINE TRUTH LOCK (Engine v3 STEP 7B)
  // ============================================================
  // CRITICAL: If data.drivers exists (even if []), use it as the ONLY source.
  // Do NOT fallback to risk_factors/factors when drivers is an empty array.
  // Empty drivers array is VALID (low-risk, diffuse risk cases).
  // ============================================================
  let canonicalDrivers: Array<{ name?: string; impact?: unknown; description?: string; [key: string]: unknown }> = [];
  let canonicalDriversFrom = 'empty';

  if (Array.isArray(data.drivers)) {
    // Engine truth: drivers exists (even if empty) - use it exclusively
    canonicalDrivers = data.drivers;
    canonicalDriversFrom = 'drivers';
  } else {
    // Only fallback if drivers field doesn't exist (undefined/null)
    // This handles legacy responses that don't have drivers field yet
    if (Array.isArray(data.risk_factors) && data.risk_factors.length > 0) {
      canonicalDrivers = data.risk_factors;
      canonicalDriversFrom = 'risk_factors';
    } else if (Array.isArray(data.factors) && data.factors.length > 0) {
      canonicalDrivers = data.factors;
      canonicalDriversFrom = 'factors';
    }
  }

  // Normalize and validate drivers (Engine v3 STEP 7B compliance)
  const normalizedDrivers: Array<{ name: string; impact: number; description: string }> = [];
  
  for (const driver of canonicalDrivers) {
    // Filter out invalid drivers (do NOT create placeholders)
    const driverName = driver?.name;
    if (!driverName || typeof driverName !== 'string' || driverName.trim() === '') {
      // Skip drivers with invalid/missing names (Engine rule: never emit placeholders)
      continue;
    }

    // Check for placeholder names (Engine rule: never emit placeholders)
    const placeholderNames = ['unknown', 'other', 'misc', 'n/a', 'none'];
    if (placeholderNames.includes(driverName.toLowerCase().trim())) {
      continue;
    }

    // Impact handling: Engine v3 impact is already 0-100 (1 decimal)
    // Safe compat: if impact <= 1, treat as 0-1 scale and scale to 0-100
    let impact = toNumber(driver?.impact, 0);
    if (impact <= 1.0 && impact > 0) {
      // Likely 0-1 scale, convert to 0-100
      impact = impact * 100;
    }
    // Clamp to [0, 100] and round to 1 decimal (Engine v3 precision)
    impact = round(clamp(impact, 0, 100), 1);

    // Skip zero-impact drivers
    if (impact <= 0) {
      continue;
    }

    normalizedDrivers.push({
      name: driverName.trim(),
      impact,
      description: toString(driver?.description, ''),
    });
  }

  // Validation: Warn if drivers.length > 3 (Engine rule: MAX_DRIVERS = 3)
  if (normalizedDrivers.length > 3) {
    warnings.push(`Driver count exceeds Engine v3 limit (${normalizedDrivers.length} > 3) - this violates engine contract`);
  }

  // Validation: Warn if impact sum is outside 95-105% (relative logic check)
  const impactSum = normalizedDrivers.reduce((sum, d) => sum + d.impact, 0);
  if (normalizedDrivers.length > 0) {
    if (impactSum < 95 || impactSum > 105) {
      warnings.push(
        `Driver impact sum (${impactSum.toFixed(1)}%) is outside expected range [95%, 105%] - relative logic may be violated`
      );
    }
  }

  // ============================================================
  // SHIPMENT INFORMATION
  // ============================================================
  const shipment = data.shipment ?? {};
  const etd = shipment.etd;
  const eta = shipment.eta;

  // Validate dates
  const validEtd = isValidISODate(etd) ? toString(etd) : undefined;
  const validEta = isValidISODate(eta) ? toString(eta) : undefined;

  if (etd && !validEtd) {
    warnings.push(`Invalid ETD date: ${etd}`);
  }
  if (eta && !validEta) {
    warnings.push(`Invalid ETA date: ${eta}`);
  }

  const shipmentViewModel = {
    id: toString(shipment.id, `SH-${Date.now()}`),
    route: toString(shipment.route, ''),
    pol: toString(shipment.pol_code ?? shipment.origin, ''),
    pod: toString(shipment.pod_code ?? shipment.destination, ''),
    carrier: toString(shipment.carrier, ''),
    etd: validEtd,
    eta: validEta,
    transitTime: round(toNumber(shipment.transit_time, 0), 0),
    container: toString(shipment.container, ''),
    cargo: toString(shipment.cargo, ''),
    incoterm: toString(shipment.incoterm, ''),
    cargoValue: round(toNumber(shipment.cargo_value ?? shipment.value, 0), 2),
  };

  // ============================================================
  // RISK SCORE VIEW MODEL
  // ============================================================
  const riskScoreViewModel = {
    score: canonicalRiskScore,
    level: canonicalRiskLevel,
    confidence: canonicalConfidence,
  };

  // ============================================================
  // PROFILE VIEW MODEL
  // ============================================================
  const profileData = data.profile ?? {};
  const profileFactors = profileData.factors ?? {};

  // Normalize factors to 0-100
  const normalizedFactors: Record<string, number> = {};
  for (const [key, value] of Object.entries(profileFactors)) {
    normalizedFactors[key] = round(toPercent(value), 0);
  }

  const profileViewModel = {
    score: round(toPercent(profileData.score ?? canonicalRiskScore), 1),
    level: normalizeRiskLevel(profileData.level ?? canonicalRiskLevel),
    confidence: round(toPercent(profileData.confidence ?? canonicalConfidence), 0),
    explanation: toArray<string>(profileData.explanation, []),
    factors: normalizedFactors,
    matrix: {
      probability: clamp(Math.round(toNumber(profileData.matrix?.probability, 5)), 1, 9),
      severity: clamp(Math.round(toNumber(profileData.matrix?.severity, 5)), 1, 9),
      quadrant: toString(profileData.matrix?.quadrant, 'Medium-Medium'),
      description: toString(profileData.matrix?.description, ''),
    },
  };

  // ============================================================
  // REASONING: Engine-generated explanation (STEP 7B.2)
  // ============================================================
  // Engine v3 STEP 7B.2: reasoning.explanation is driver-based, not factor-based
  // This aligns with structured drivers and provides narrative context
  const reasoningData = (data.reasoning as { explanation?: unknown } | undefined) ?? {};
  const reasoningExplanation = toString(reasoningData.explanation, '');
  
  const reasoningViewModel = {
    explanation: reasoningExplanation,
  };

  // ============================================================
  // LAYERS
  // ============================================================
  const layers = toArray<{ name?: unknown; score?: unknown; contribution?: unknown; [key: string]: unknown }>(data.layers, []);
  const normalizedLayers = layers.map((layer) => ({
    name: toString(layer?.name, 'Unknown Layer'),
    score: round(toPercent(layer?.score), 1),
    contribution: round(toPercent(layer?.contribution), 0),
  }));

  // ============================================================
  // TIMELINE (Risk Scenario Projections)
  // ============================================================
  const projections = toArray<{ date?: unknown; p10?: unknown; p50?: unknown; p90?: unknown; phase?: unknown; [key: string]: unknown }>(data.riskScenarioProjections, []);
  const normalizedProjections = projections.map((proj) => {
    const p10 = round(toPercent(proj?.p10), 1);
    const p50 = round(toPercent(proj?.p50), 1);
    const p90 = round(toPercent(proj?.p90), 1);

    // Ensure p10 <= p50 <= p90
    const sorted = [p10, p50, p90].sort((a, b) => a - b);
    const repaired = {
      p10: sorted[0] as number,
      p50: sorted[1] as number,
      p90: sorted[2] as number,
    };

    // Warn if ordering was violated
    const projDate = proj?.date;
    if (p10 > p50 || p50 > p90) {
      warnings.push(`Timeline projection ordering violation at ${projDate ? toString(projDate) : 'unknown date'} - repaired`);
    }

    const dateStr: string = isValidISODate(projDate) ? toString(projDate) : new Date().toISOString().split('T')[0]!;

    return {
      date: dateStr,
      p10: repaired.p10,
      p50: repaired.p50,
      p90: repaired.p90,
      phase: toString(proj?.phase, 'Unknown'),
    };
  });

  const timelineViewModel = {
    projections: normalizedProjections,
    hasData: normalizedProjections.length > 0,
  };

  // ============================================================
  // LOSS METRICS
  // ============================================================
  let lossViewModel: { p95: number; p99: number; expectedLoss: number; tailContribution: number } | null = null;

  if (data.loss) {
    const loss = data.loss;
    // Support multiple field naming conventions
    const p95 = toNumber(loss.p95 ?? loss.var95 ?? loss.var_95 ?? loss.VaR95, 0);
    const p99 = toNumber(loss.p99 ?? loss.cvar99 ?? loss.cvar_99 ?? loss.CVaR99, 0);
    const expectedLoss = toNumber(loss.expectedLoss ?? loss.expected_loss ?? loss.el ?? loss.EL, 0);
    // tailContribution is optional - default to 0 if not provided
    const rawTailContribution = loss.tailContribution ?? loss.tail_contribution;
    const tailContribution = rawTailContribution !== undefined && rawTailContribution !== null
      ? round(toPercent(rawTailContribution), 1)
      : 0;

    // Clamp to non-negative and warn if negative
    if (p95 < 0 || p99 < 0 || expectedLoss < 0) {
      warnings.push('Loss metrics contain negative values - clamped to 0');
    }

    lossViewModel = {
      p95: round(Math.max(0, p95), 2),
      p99: round(Math.max(0, p99), 2),
      expectedLoss: round(Math.max(0, expectedLoss), 2),
      tailContribution,
    };
  }

  // ============================================================
  // SCENARIOS
  // ============================================================
  const scenarios = toArray<{ id?: unknown; title?: unknown; category?: unknown; riskReduction?: unknown; costImpact?: unknown; isRecommended?: unknown; rank?: unknown; description?: unknown; [key: string]: unknown }>(data.scenarios, []);
  const normalizedScenarios = scenarios.map((scenario, index) => {
    // Generate stable ID if missing
    let id = toString(scenario?.id, '');
    if (!id) {
      const title = toString(scenario?.title, '');
      id = title ? slugify(title) : `scenario-${index}`;
    }

    return {
      id,
      title: toString(scenario?.title, 'Untitled Scenario'),
      category: toString(scenario?.category, 'UNKNOWN'),
      riskReduction: round(toNumber(scenario?.riskReduction, 0), 1),
      costImpact: round(toNumber(scenario?.costImpact, 0), 2),
      isRecommended: Boolean(scenario?.isRecommended),
      rank: Math.round(toNumber(scenario?.rank, 99)),
      description: toString(scenario?.description, ''),
    };
  });

  // ============================================================
  // DECISIONS
  // ============================================================
  const decisionSummary = data.decision_summary ?? {};

  // Insurance decision
  const insurance = decisionSummary.insurance ?? {};
  const insuranceViewModel = {
    status: (toString(insurance.status, 'UNKNOWN') as 'RECOMMENDED' | 'OPTIONAL' | 'NOT_NEEDED' | 'UNKNOWN') || 'UNKNOWN',
    recommendation: (toString(insurance.recommendation, 'N/A') as 'BUY' | 'CONSIDER' | 'SKIP' | 'N/A') || 'N/A',
    rationale: toString(insurance.rationale, 'No rationale provided'),
    riskDeltaPoints: insurance.risk_delta_points !== null && insurance.risk_delta_points !== undefined
      ? round(toNumber(insurance.risk_delta_points), 1)
      : null,
    costImpactUsd: insurance.cost_impact_usd !== null && insurance.cost_impact_usd !== undefined
      ? round(toNumber(insurance.cost_impact_usd), 2)
      : null,
    providers: toArray(insurance.providers, []),
  };

  // Timing decision
  const timing = decisionSummary.timing ?? {};
  const optimalWindow = timing.optimal_window;
  let timingOptimalWindow: { start: string; end: string } | null = null;

  if (optimalWindow && optimalWindow.start && optimalWindow.end) {
    const start = toString(optimalWindow.start);
    const end = toString(optimalWindow.end);

    if (isValidISODate(start) && isValidISODate(end)) {
      timingOptimalWindow = { start, end };
    } else {
      warnings.push(`Invalid timing optimal window dates: ${start}, ${end}`);
    }
  }

  // Also check top-level timing field
  const topLevelTiming = data.timing;
  if (topLevelTiming?.optimalWindow) {
    const window = topLevelTiming.optimalWindow;
    if (window?.start && window?.end) {
      const start = toString(window.start);
      const end = toString(window.end);
      if (isValidISODate(start) && isValidISODate(end)) {
        timingOptimalWindow = { start, end };
      }
    }
  }

  const timingViewModel = {
    status: (toString(timing.status, 'UNKNOWN') as 'RECOMMENDED' | 'OPTIONAL' | 'NOT_NEEDED' | 'UNKNOWN') || 'UNKNOWN',
    recommendation: (toString(timing.recommendation, 'N/A') as 'ADJUST_ETD' | 'KEEP_ETD' | 'N/A') || 'N/A',
    rationale: toString(timing.rationale, 'No rationale provided'),
    optimalWindow: timingOptimalWindow,
    riskReductionPoints: timing.risk_reduction_points !== null && timing.risk_reduction_points !== undefined
      ? round(toNumber(timing.risk_reduction_points), 1)
      : null,
    costImpactUsd: timing.cost_impact_usd !== null && timing.cost_impact_usd !== undefined
      ? round(toNumber(timing.cost_impact_usd), 2)
      : null,
  };

  // Routing decision
  const routing = decisionSummary.routing ?? {};
  const routingViewModel = {
    status: (toString(routing.status, 'UNKNOWN') as 'RECOMMENDED' | 'OPTIONAL' | 'NOT_NEEDED' | 'UNKNOWN') || 'UNKNOWN',
    recommendation: (toString(routing.recommendation, 'N/A') as 'CHANGE_ROUTE' | 'KEEP_ROUTE' | 'N/A') || 'N/A',
    rationale: toString(routing.rationale, 'No rationale provided'),
    bestAlternative: routing.best_alternative !== null && routing.best_alternative !== undefined
      ? toString(routing.best_alternative)
      : null,
    tradeoff: routing.tradeoff !== null && routing.tradeoff !== undefined
      ? toString(routing.tradeoff)
      : null,
    riskReductionPoints: routing.risk_reduction_points !== null && routing.risk_reduction_points !== undefined
      ? round(toNumber(routing.risk_reduction_points), 1)
      : null,
    costImpactUsd: routing.cost_impact_usd !== null && routing.cost_impact_usd !== undefined
      ? round(toNumber(routing.cost_impact_usd), 2)
      : null,
  };

  const decisionsViewModel = {
    insurance: insuranceViewModel,
    timing: timingViewModel,
    routing: routingViewModel,
  };

  // ============================================================
  // METADATA
  // ============================================================
  const metaViewModel = {
    warnings,
    source: {
      canonicalRiskScoreFrom,
      canonicalDriversFrom,
    },
    engineVersion: toString(data.engine_version, 'v2'),
    language: toString(data.language, 'en'),
    timestamp: isValidISODate(data.timestamp) ? toString(data.timestamp) : undefined,
  };

  // ============================================================
  // RETURN COMPLETE VIEW MODEL (SLICE-BASED STRUCTURE)
  // ============================================================
  return {
    overview: {
      shipment: shipmentViewModel,
      riskScore: riskScoreViewModel,
      profile: profileViewModel,
      reasoning: reasoningViewModel,
    },
    breakdown: {
      layers: normalizedLayers,
      factors: normalizedFactors,
    },
    timeline: timelineViewModel,
    decisions: decisionsViewModel,
    loss: lossViewModel,
    scenarios: normalizedScenarios,
    drivers: normalizedDrivers,
    meta: metaViewModel,
  };
}

/**
 * Create default view model with warnings
 * Used when input is invalid
 */
function createDefaultViewModel(warnings: string[]): ResultsViewModel {
  return {
    overview: {
      shipment: {
        id: `SH-${Date.now()}`,
        route: '',
        pol: '',
        pod: '',
        carrier: '',
        etd: undefined,
        eta: undefined,
        transitTime: 0,
        container: '',
        cargo: '',
        incoterm: '',
        cargoValue: 0,
      },
      riskScore: {
        score: 0,
        level: 'Unknown',
        confidence: 0,
      },
      profile: {
        score: 0,
        level: 'Unknown',
        confidence: 0,
        explanation: [],
        factors: {},
        matrix: {
          probability: 5,
          severity: 5,
          quadrant: 'Medium-Medium',
          description: '',
        },
      },
      reasoning: {
        explanation: '',
      },
    },
    breakdown: {
      layers: [],
      factors: {},
    },
    timeline: {
      projections: [],
      hasData: false,
    },
    loss: null,
    scenarios: [],
    drivers: [],
    decisions: {
      insurance: {
        status: 'UNKNOWN',
        recommendation: 'N/A',
        rationale: 'No data available',
        riskDeltaPoints: null,
        costImpactUsd: null,
        providers: [],
      },
      timing: {
        status: 'UNKNOWN',
        recommendation: 'N/A',
        rationale: 'No data available',
        optimalWindow: null,
        riskReductionPoints: null,
        costImpactUsd: null,
      },
      routing: {
        status: 'UNKNOWN',
        recommendation: 'N/A',
        rationale: 'No data available',
        bestAlternative: null,
        tradeoff: null,
        riskReductionPoints: null,
        costImpactUsd: null,
      },
    },
    meta: {
      warnings,
      source: {
        canonicalRiskScoreFrom: 'default',
        canonicalDriversFrom: 'empty',
      },
      engineVersion: 'v2',
      language: 'en',
      timestamp: undefined,
    },
  };
}

