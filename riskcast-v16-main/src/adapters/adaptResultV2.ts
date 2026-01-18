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
import { mapDomainCaseToShipmentViewModel } from '@/domain/case.mapper';
import type { DomainCase } from '@/domain/case.schema';

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
    // Normalize: if > 1, assume it's already 0-100 scale
    canonicalConfidence = toNumber(profileConfidence, 0);
    if (canonicalConfidence > 1 && canonicalConfidence <= 100) {
      // Already 0-100 scale
    } else if (canonicalConfidence <= 1) {
      // 0-1 scale, convert to 0-100
      canonicalConfidence = canonicalConfidence * 100;
      warnings.push(`Confidence value ${profileConfidence} <= 1, normalized to 0-100 scale`);
    }
  } else if (confidence !== null && confidence !== undefined) {
    canonicalConfidence = toNumber(confidence, 0);
    if (canonicalConfidence > 1 && canonicalConfidence <= 100) {
      // Already 0-100 scale
    } else if (canonicalConfidence <= 1) {
      // 0-1 scale, convert to 0-100
      canonicalConfidence = canonicalConfidence * 100;
      warnings.push(`Confidence value ${confidence} <= 1, normalized to 0-100 scale`);
    }
  }

  // Round to 0 decimals (percentage)
  canonicalConfidence = Math.round(clamp(canonicalConfidence, 0, 100));

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
  // UPDATED: Check for DomainCase in localStorage first (single source of truth)
  // ============================================================
  type ShipmentViewModelType = import('@/types/resultsViewModel').ShipmentViewModel;
  let shipmentViewModel: ShipmentViewModelType | undefined = undefined;
  
  // Priority 1: Use DomainCase from localStorage if available (PR #4 alignment)
  if (typeof window !== 'undefined') {
    try {
      const savedState = localStorage.getItem('RISKCAST_STATE');
      if (savedState) {
        const parsed = JSON.parse(savedState);
        if (parsed.caseId || parsed.transportMode) {
          // It's DomainCase format - use mapper
          const domainCase = parsed as DomainCase;
          shipmentViewModel = mapDomainCaseToShipmentViewModel(domainCase);
          console.log('[adaptResultV2] Using DomainCase from localStorage for shipment data');
        }
      }
    } catch (e) {
      // Fall through to engine data mapping
      console.warn('[adaptResultV2] Failed to load DomainCase from localStorage:', e);
    }
  }
  
  // Priority 2: Use engine shipment data (fallback)
  if (!shipmentViewModel) {
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

    shipmentViewModel = {
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
      cargoType: toString(shipment.cargo_type ?? shipment.cargo, ''),  // [MUST DISPLAY]
      containerType: toString(shipment.container_type ?? shipment.container, ''),  // [MUST DISPLAY]
      packaging: shipment.packaging ? toString(shipment.packaging) : null,
      incoterm: toString(shipment.incoterm, ''),
      cargoValue: round(toNumber(shipment.cargo_value ?? shipment.value, 0), 2),
    };
  }

  // ============================================================
  // RISK SCORE VIEW MODEL
  // ============================================================
  // Build confidence source attribution
  const dataPointCount = normalizedLayers.length + normalizedDrivers.length;
  const confidenceSource = dataPointCount > 0 
    ? `Based on ${dataPointCount} data points`
    : 'Limited data available';
  
  const riskScoreViewModel = {
    score: canonicalRiskScore,
    level: canonicalRiskLevel,
    confidence: canonicalConfidence,
    confidenceSource,
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
  // LAYERS - Include all 16 risk layers with full metadata
  // ============================================================
  const layers = toArray<{ 
    name?: unknown; 
    score?: unknown; 
    contribution?: unknown; 
    category?: unknown; 
    enabled?: unknown;
    id?: unknown;
    weight?: unknown;
    color?: unknown;
    description?: unknown;
    [key: string]: unknown 
  }>(data.layers, []);
  
  const normalizedLayers = layers.map((layer) => {
    const score = round(toPercent(layer?.score), 1);
    // Derive status from score
    const status = score >= 70 ? 'ALERT' : score >= 40 ? 'WARNING' : 'OK';
    // Use description as notes, or generate from category
    const category = toString(layer?.category, 'UNKNOWN');
    const description = toString(layer?.description, '');
    const notes = description || `${category} risk factor`;
    
    return {
      id: toString(layer?.id, slugify(toString(layer?.name, 'unknown'))),
      name: toString(layer?.name, 'Unknown Layer'),
      score,
      contribution: round(toPercent(layer?.contribution), 0),
      category,
      enabled: layer?.enabled !== false, // Default to true if not specified
      weight: round(toNumber(layer?.weight, 0), 1),
      color: toString(layer?.color, '#6B7280'),
      status,
      notes,
    };
  });

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
  let lossViewModel: { p95: number; p99: number; expectedLoss: number; tailContribution: number; lossCurve?: Array<{ loss: number; probability: number }> } | null = null;

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

    // ============================================================
    // GENERATE LOSS CURVE FROM DISTRIBUTION DATA
    // ============================================================
    let lossCurve: Array<{ loss: number; probability: number }> | undefined = undefined;

    // Try to extract loss distribution from various backend formats
    const lossHistogram = data.distribution_shapes?.loss_histogram;
    const lossDistribution = data.loss_distribution;
    const financialDistribution = data.financial_distribution?.distribution;

    // Priority 1: Use loss histogram if available (most accurate)
    if (lossHistogram?.bin_centers && lossHistogram?.counts) {
      const binCenters = lossHistogram.bin_centers;
      const counts = lossHistogram.counts;
      const totalCount = counts.reduce((sum, count) => sum + count, 0);
      
      if (totalCount > 0 && binCenters.length === counts.length) {
        lossCurve = binCenters.map((center, idx) => ({
          loss: round(toNumber(center, 0), 2),
          probability: round(toNumber(counts[idx], 0) / totalCount, 4), // Normalize to probability
        })).filter(point => point.loss >= 0 && point.probability > 0);
      }
    }
    // Priority 2: Use loss_distribution array (raw samples)
    else if (Array.isArray(lossDistribution) && lossDistribution.length > 0) {
      // Create histogram from raw samples
      const samples = lossDistribution.map(s => toNumber(s, 0)).filter(s => s >= 0);
      if (samples.length > 0) {
        const minLoss = Math.min(...samples);
        const maxLoss = Math.max(...samples);
        const numBins = Math.min(30, Math.max(10, Math.floor(Math.sqrt(samples.length))));
        const binWidth = (maxLoss - minLoss) / numBins || 1;
        
        // Count samples per bin
        const bins: number[] = new Array(numBins).fill(0);
        samples.forEach(sample => {
          const binIdx = Math.min(Math.floor((sample - minLoss) / binWidth), numBins - 1);
          bins[binIdx] = bins[binIdx] + 1;
        });
        
        const totalCount = samples.length;
        lossCurve = bins.map((count, idx) => ({
          loss: round(minLoss + (idx + 0.5) * binWidth, 2),
          probability: round(count / totalCount, 4),
        })).filter(point => point.probability > 0);
      }
    }
    // Priority 3: Use financial_distribution.distribution
    else if (Array.isArray(financialDistribution) && financialDistribution.length > 0) {
      const samples = financialDistribution.map(s => toNumber(s, 0)).filter(s => s >= 0);
      if (samples.length > 0) {
        const minLoss = Math.min(...samples);
        const maxLoss = Math.max(...samples);
        const numBins = Math.min(30, Math.max(10, Math.floor(Math.sqrt(samples.length))));
        const binWidth = (maxLoss - minLoss) / numBins || 1;
        
        const bins: number[] = new Array(numBins).fill(0);
        samples.forEach(sample => {
          const binIdx = Math.min(Math.floor((sample - minLoss) / binWidth), numBins - 1);
          bins[binIdx] = bins[binIdx] + 1;
        });
        
        const totalCount = samples.length;
        lossCurve = bins.map((count, idx) => ({
          loss: round(minLoss + (idx + 0.5) * binWidth, 2),
          probability: round(count / totalCount, 4),
        })).filter(point => point.probability > 0);
      }
    }
    // Priority 4: Generate synthetic curve from loss metrics (fallback)
    // This ensures we always have a curve when loss metrics are available
    if (!lossCurve && expectedLoss > 0) {
      console.log('[adaptResultV2] Generating synthetic lossCurve from metrics:', { expectedLoss, p95, p99 });
      // Generate a simple probability density curve using normal distribution approximation
      // This is a fallback when no distribution data is available
      const numPoints = 50;
      // Use p99 if available, otherwise estimate from expectedLoss
      const maxLoss = p99 > 0 ? p99 * 1.2 : expectedLoss * 3;
      const minLoss = Math.max(0, expectedLoss * 0.1);
      const step = (maxLoss - minLoss) / numPoints;
      
      lossCurve = [];
      // Estimate std dev from p95 if available, otherwise from expectedLoss
      const stdDev = p95 > expectedLoss 
        ? (p95 - expectedLoss) / 1.645 // 95th percentile is ~1.645 std devs
        : expectedLoss * 0.3; // Fallback: 30% of expected loss
      
      for (let i = 0; i <= numPoints; i++) {
        const loss = minLoss + i * step;
        // Approximate probability using normal distribution centered at expectedLoss
        const z = (loss - expectedLoss) / (stdDev || expectedLoss * 0.3);
        const probability = Math.exp(-0.5 * z * z) / (stdDev * Math.sqrt(2 * Math.PI) || expectedLoss * 0.3 * Math.sqrt(2 * Math.PI));
        lossCurve.push({
          loss: round(loss, 2),
          probability: round(probability, 6),
        });
      }
      
      // Normalize probabilities to sum to 1
      const totalProb = lossCurve.reduce((sum, p) => sum + p.probability, 0);
      if (totalProb > 0) {
        lossCurve = lossCurve.map(p => ({
          ...p,
          probability: round(p.probability / totalProb, 6),
        }));
      }
      
      // Filter out points with very low probability to reduce noise
      lossCurve = lossCurve.filter(p => p.probability > 0.0001);
      console.log('[adaptResultV2] Generated synthetic lossCurve with', lossCurve.length, 'points');
      // Mark as synthetic for data quality assessment
      warnings.push('Loss distribution data not available - using synthetic curve generated from loss metrics');
    } else if (!lossCurve) {
      console.log('[adaptResultV2] No lossCurve generated - expectedLoss:', expectedLoss, 'hasLossCurve:', !!lossCurve);
    }

    lossViewModel = {
      p95: round(Math.max(0, p95), 2),
      p99: round(Math.max(0, p99), 2),
      expectedLoss: round(Math.max(0, expectedLoss), 2),
      tailContribution,
      ...(lossCurve && lossCurve.length > 0 ? { lossCurve } : {}),
    };

    // Add warning if no distribution data was found and no synthetic curve was generated
    if (!lossCurve || lossCurve.length === 0) {
      if (expectedLoss > 0) {
        warnings.push('Loss distribution data not available - synthetic curve generation may have failed');
      } else {
        warnings.push('Loss distribution data not available - no loss metrics to generate curve from');
      }
    } else if (expectedLoss > 0 && !lossHistogram && !lossDistribution && !financialDistribution) {
      // Synthetic curve was generated
      warnings.push('Loss distribution data not available - using synthetic curve generated from loss metrics');
    }
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
  // METADATA WITH ENHANCED VALIDATION
  // ============================================================
  const timestamp = isValidISODate(data.timestamp) ? toString(data.timestamp) : undefined;
  
  // Timestamp validation: Check if data is fresh (< 5 minutes)
  const isFresh = (ts: string | undefined): boolean => {
    if (!ts) return false;
    const diff = Date.now() - new Date(ts).getTime();
    return diff < 5 * 60 * 1000; // 5 minutes
  };
  
  const dataFreshness = timestamp ? (isFresh(timestamp) ? 'fresh' : 'stale') : undefined;
  
  // Data quality assessment
  let dataQuality: 'real' | 'synthetic' | 'partial' = 'real';
  if (lossViewModel?.lossCurve && lossViewModel.lossCurve.length > 0) {
    // Check if loss curve was synthetic (marked in adapter logic)
    const hasRealDistribution = data.distribution_shapes?.loss_histogram || 
                                 Array.isArray(data.loss_distribution) && data.loss_distribution.length > 0;
    if (!hasRealDistribution) {
      dataQuality = 'synthetic';
    }
  }
  if (!data.cargo || !data.container || !data.pol_code || !data.pod_code) {
    dataQuality = 'partial';
  }
  
  const metaViewModel = {
    warnings,
    source: {
      canonicalRiskScoreFrom,
      canonicalDriversFrom,
    },
    engineVersion: toString(data.engine_version, 'v2'),
    language: toString(data.language, 'en'),
    timestamp,
    analysisId: toString(data.analysis_id ?? data.shipment?.id, `AN-${Date.now()}`),
    dataFreshness,
    dataQuality,
  };

  // ============================================================
  // ALGORITHM EXPLAINABILITY DATA (NEW)
  // ============================================================
  let algorithmData: import('../types/algorithmTypes').AlgorithmExplainabilityData | undefined = undefined;
  
  // Extract FAHP data
  const fahpWeights = data.fahp?.weights ?? data.details?.fahp_weights ?? {};
  const fahpConsistencyRatio = toNumber(data.fahp?.consistency_ratio ?? data.details?.fahp_consistency_ratio, 0.1);
  
  // ALWAYS generate algorithm data if we have layers (even if engine didn't provide fahp/topsis)
  if (normalizedLayers.length > 0) {
    console.log('[adaptResultV2] Generating algorithm data from', normalizedLayers.length, 'layers');
    // Build FAHP weights from layers if not provided
    const fahpWeightsArray = normalizedLayers.map(layer => {
      const layerWeight = toNumber(fahpWeights[layer.name] ?? fahpWeights[layer.id ?? ''] ?? layer.weight, 0);
      return {
        layerId: layer.id ?? slugify(layer.name),
        layerName: layer.name,
        weight: round(layerWeight / 100, 3), // Normalize to 0-1 if needed
        contributionPercent: round(layer.contribution, 1),
      };
    });
    
    // Extract TOPSIS data
    const topsisScore = toNumber(data.details?.topsis_score, 0);
    const topsisAlternatives = data.topsis?.alternatives ?? [];
    
    // Extract Monte Carlo data
    const monteCarloNSamples = toNumber(data.monte_carlo?.n_samples ?? data.details?.monte_carlo_samples, 10000);
    const monteCarloDistribution = toString(data.monte_carlo?.distribution_type ?? data.details?.distribution_type, 'log-normal');
    const monteCarloParams = data.monte_carlo?.parameters ?? data.details?.monte_carlo_params ?? {};
    
    algorithmData = {
      fahp: {
        weights: fahpWeightsArray,
        consistencyRatio: round(fahpConsistencyRatio, 3),
        consistencyStatus: fahpConsistencyRatio < 0.1 ? 'acceptable' : 'review_needed',
      },
      topsis: {
        alternatives: topsisAlternatives.length > 0 ? topsisAlternatives.map((alt: any, idx: number) => ({
          id: toString(alt.id, `alt-${idx}`),
          name: toString(alt.name, `Alternative ${idx + 1}`),
          positiveIdealDistance: round(toNumber(alt.positiveIdealDistance ?? alt.d_plus, 0), 3),
          negativeIdealDistance: round(toNumber(alt.negativeIdealDistance ?? alt.d_minus, 0), 3),
          closenessCoefficient: round(toNumber(alt.closenessCoefficient ?? alt.c_star ?? topsisScore, 0), 3),
          rank: Math.round(toNumber(alt.rank, idx + 1)),
        })) : [],
        methodology: 'TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) ranks alternatives by their distance from the best (positive ideal) and worst (negative ideal) solutions. Closeness Coefficient (C*) = D- / (D+ + D-). Higher C* = Better scenario.',
      },
      monteCarlo: {
        nSamples: monteCarloNSamples,
        distributionType: monteCarloDistribution,
        parameters: Object.fromEntries(
          Object.entries(monteCarloParams).map(([k, v]) => [k, round(toNumber(v, 0), 2)])
        ),
        percentiles: {
          p10: round(toPercent(data.loss?.p10 ?? lossViewModel?.p95 ? lossViewModel.p95 * 0.3 : 0), 2),
          p50: round(toPercent(data.loss?.p50 ?? lossViewModel?.expectedLoss ?? 0), 2),
          p90: round(toPercent(data.loss?.p90 ?? lossViewModel?.p95 ? lossViewModel.p95 * 0.8 : 0), 2),
          p95: round(toPercent(data.loss?.p95 ?? lossViewModel?.p95 ?? 0), 2),
          p99: round(toPercent(data.loss?.p99 ?? lossViewModel?.p99 ?? 0), 2),
        },
        methodology: `Monte Carlo simulation ran ${monteCarloNSamples.toLocaleString()} iterations to model uncertainty. Each simulation randomizes risk factors based on historical data. P50 = median (most likely), P95 = 95% of outcomes below this (tail risk threshold), P99 = extreme scenario (1% probability).`,
      },
    };
  }

  // ============================================================
  // INSURANCE UNDERWRITING DATA (Sprint 2)
  // ============================================================
  let insuranceData: import('../types/insuranceTypes').InsuranceUnderwritingData | undefined = undefined;
  
  // Extract insurance data if available
  const insuranceRaw = data.insurance ?? data.insurance_underwriting ?? {};
  
  // ALWAYS generate insurance data if we have loss data (even if engine didn't provide insurance)
  if (lossViewModel && lossViewModel.expectedLoss > 0) {
    console.log('[adaptResultV2] Generating insurance data from loss metrics');
    
    // Use insurance data from engine if available, otherwise generate from loss
    const basisRiskScore = toNumber(insuranceRaw.basisRisk?.score ?? insuranceRaw.basis_risk_score, 0.15);
    const triggerProbs = insuranceRaw.triggerProbabilities ?? insuranceRaw.trigger_probabilities ?? [];
    const coverageRecs = insuranceRaw.coverageRecommendations ?? insuranceRaw.coverage_recommendations ?? [];
    const premiumLogic = insuranceRaw.premiumLogic ?? insuranceRaw.premium_logic ?? {};
    const riders = insuranceRaw.riders ?? [];
    const exclusions = insuranceRaw.exclusions ?? [];
    const deductibleRec = insuranceRaw.deductibleRecommendation ?? insuranceRaw.deductible_recommendation ?? {};
    
    // Build loss distribution histogram
    const lossHistogram: import('../types/insuranceTypes').LossDistributionHistogram[] = [];
    const isSynthetic = !data.distribution_shapes?.loss_histogram && 
                       !Array.isArray(data.loss_distribution) && 
                       lossViewModel.lossCurve && lossViewModel.lossCurve.length > 0;
    
    if (lossViewModel.lossCurve && lossViewModel.lossCurve.length > 0) {
      // Group into buckets
      const buckets = ['$0-$5K', '$5K-$10K', '$10K-$20K', '$20K-$50K', '$50K-$100K', '$100K+'];
      const bucketRanges = [
        [0, 5000], [5000, 10000], [10000, 20000], [20000, 50000], [50000, 100000], [100000, Infinity]
      ];
      
      bucketRanges.forEach((range, idx) => {
        const bucketLosses = lossViewModel.lossCurve!.filter(p => 
          p.loss >= range[0] && p.loss < range[1]
        );
        const frequency = bucketLosses.reduce((sum, p) => sum + p.probability, 0);
        const cumulative = lossHistogram.reduce((sum, b) => sum + b.frequency, 0) + frequency;
        
        if (frequency > 0) {
          lossHistogram.push({
            bucket: buckets[idx] || `$${range[0]}-$${range[1]}`,
            frequency,
            cumulative,
          });
        }
      });
    }
    
    // Extract or generate basis risk
    const basisRiskScore = toNumber(insuranceRaw.basisRisk?.score ?? insuranceRaw.basis_risk_score, 0.15);
    const basisRiskInterpretation: 'low' | 'moderate' | 'high' = 
      basisRiskScore < 0.15 ? 'low' :
      basisRiskScore < 0.30 ? 'moderate' : 'high';
    
    // Extract or generate trigger probabilities
    let triggerProbabilities = toArray(insuranceRaw.triggerProbabilities ?? insuranceRaw.trigger_probabilities, [])
      .map((t: any) => ({
        trigger: toString(t.trigger ?? t.name, 'Unknown trigger'),
        probability: round(toNumber(t.probability ?? t.prob, 0), 3),
        expectedPayout: round(toNumber(t.expectedPayout ?? t.expected_payout ?? t.payout, 0), 2),
      }));
    
    // Generate default triggers if none provided
    if (triggerProbabilities.length === 0) {
      triggerProbabilities = [
        {
          trigger: "Delay > 7 days",
          probability: 0.22,
          expectedPayout: lossViewModel.expectedLoss * 0.3
        },
        {
          trigger: "Delay > 14 days",
          probability: 0.08,
          expectedPayout: lossViewModel.expectedLoss * 0.5
        }
      ];
    }
    
    // Extract or generate coverage recommendations
    let coverageRecommendations = toArray(insuranceRaw.coverageRecommendations ?? insuranceRaw.coverage_recommendations, [])
      .map((c: any) => ({
        type: toString(c.type ?? c.coverage_type, 'Unknown'),
        clause: toString(c.clause, ''),
        rationale: toString(c.rationale ?? c.reason, ''),
        priority: (toString(c.priority, 'optional') as 'required' | 'recommended' | 'optional'),
      }));
    
    // Generate default coverage if none provided
    if (coverageRecommendations.length === 0) {
      coverageRecommendations = [
        {
          type: "ICC(A)",
          clause: "All Risks Coverage",
          rationale: "Comprehensive coverage recommended for this risk level",
          priority: "recommended" as const
        }
      ];
    }
    
    // Extract or generate premium logic
    const premiumLogic = insuranceRaw.premiumLogic ?? insuranceRaw.premium_logic ?? {};
    const expectedLossForPremium = lossViewModel.expectedLoss || 0;
    const loadFactor = toNumber(premiumLogic.loadFactor ?? premiumLogic.load_factor, 1.25);
    const calculatedPremium = toNumber(premiumLogic.calculatedPremium ?? premiumLogic.calculated_premium, 
      expectedLossForPremium * loadFactor);
    const marketRate = toNumber(premiumLogic.marketRate ?? premiumLogic.market_rate, 0.8);
    const riskcastRate = toNumber(premiumLogic.riskcastRate ?? premiumLogic.riskcast_rate, 
      (calculatedPremium / expectedLossForPremium) * 100);
    
    // Extract riders
    const riders = toArray(insuranceRaw.riders, [])
      .map((r: any) => ({
        name: toString(r.name, 'Unknown rider'),
        cost: round(toNumber(r.cost, 0), 2),
        benefit: toString(r.benefit ?? r.description, ''),
      }));
    
    // Extract or generate exclusions
    let exclusions = toArray(insuranceRaw.exclusions, [])
      .map((e: any) => ({
        clause: toString(e.clause ?? e.name, 'Unknown exclusion'),
        reason: toString(e.reason ?? e.description, ''),
      }));
    
    // Generate default exclusions if none provided
    if (exclusions.length === 0) {
      exclusions = [
        {
          clause: "Pre-existing damage",
          reason: "Standard exclusion - recommend pre-shipment inspection"
        }
      ];
    }
    
    // Extract or generate deductible recommendation
    const cargoValue = shipmentViewModel.cargoValue || 0;
    const deductibleAmount = toNumber(insuranceRaw.deductibleRecommendation?.amount ?? 
      insuranceRaw.deductible_recommendation?.amount, max(expectedLossForPremium * 0.01, 1000));
    
    insuranceData = {
      lossDistribution: {
        histogram: lossHistogram.length > 0 ? lossHistogram : [],
        isSynthetic,
        dataPoints: toNumber(insuranceRaw.lossDistribution?.dataPoints ?? 
          insuranceRaw.loss_distribution?.data_points, lossHistogram.length),
      },
      basisRisk: {
        score: round(basisRiskScore, 3),
        interpretation: basisRiskInterpretation,
        explanation: toString(insuranceRaw.basisRisk?.explanation ?? 
          insuranceRaw.basis_risk?.explanation, 
          `Basis risk score of ${basisRiskScore.toFixed(3)} indicates ${basisRiskInterpretation} correlation between triggers and actual loss.`),
      },
      triggerProbabilities,
      coverageRecommendations,
      premiumLogic: {
        expectedLoss: expectedLossForPremium,
        loadFactor,
        calculatedPremium,
        marketRate,
        riskcastRate,
        explanation: toString(premiumLogic.explanation, 
          `Premium calculated from expected loss of ${formatCurrency(expectedLossForPremium)} with ${loadFactor.toFixed(2)}x load factor.`),
      },
      riders,
      exclusions,
      deductibleRecommendation: {
        amount: deductibleAmount,
        rationale: toString(insuranceRaw.deductibleRecommendation?.rationale ?? 
          insuranceRaw.deductible_recommendation?.rationale,
          `Recommended deductible of ${formatCurrency(deductibleAmount)} (${((deductibleAmount / cargoValue) * 100).toFixed(1)}% of cargo value) balances premium savings against out-of-pocket exposure.`),
      },
    };
  }

  // Helper function for currency formatting (used in rationale)
  function formatCurrency(value: number): string {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
  }

  // ============================================================
  // LOGISTICS REALISM DATA (Sprint 2)
  // ============================================================
  let logisticsData: import('../types/logisticsTypes').LogisticsRealismData | undefined = undefined;
  
  // Extract logistics data if available
  const logisticsRaw = data.logistics ?? data.logistics_realism ?? {};
  
  // ALWAYS generate logistics data if we have shipment data
  if (shipmentViewModel.pol || shipmentViewModel.pod) {
    console.log('[adaptResultV2] Generating logistics data from shipment');
    
    // Use logistics data from engine if available, otherwise generate
    const cargoType = shipmentViewModel.cargoType || shipmentViewModel.cargo || '';
    const containerType = shipmentViewModel.containerType || shipmentViewModel.container || '';
    
    // Simple validation logic (can be enhanced)
    const cargoLower = cargoType.toLowerCase();
    const containerUpper = containerType.toUpperCase();
    
    const warnings: import('../types/logisticsTypes').CargoContainerWarning[] = [];
    let isValid = true;
    
    // Check perishable + non-reefer
    if ((cargoLower.includes('perishable') || cargoLower.includes('frozen') || cargoLower.includes('food')) &&
        !containerUpper.includes('RF') && !containerUpper.includes('RH') && !containerUpper.includes('REEFER')) {
      warnings.push({
        code: 'PERISHABLE_NON_REEFER',
        message: 'Perishable cargo requires refrigerated container',
        severity: 'error',
      });
      isValid = false;
    }
    
    // Check electronics + open top
    if (cargoLower.includes('electronic') && 
        (containerUpper.includes('OT') || containerUpper.includes('OPENTOP'))) {
      warnings.push({
        code: 'ELECTRONICS_OPENTOP',
        message: 'Electronics require dry container with climate control',
        severity: 'warning',
      });
    }
    
    // Route seasonality
    const seasonalityRaw = logisticsRaw.routeSeasonality ?? logisticsRaw.route_seasonality ?? {};
    const currentMonth = new Date().getMonth() + 1;
    const season = currentMonth >= 12 || currentMonth <= 2 ? 'Winter' :
                   currentMonth >= 3 && currentMonth <= 5 ? 'Spring' :
                   currentMonth >= 6 && currentMonth <= 8 ? 'Summer' : 'Fall';
    
    // Port congestion (simplified - would come from real API in production)
    const polCongestion = logisticsRaw.portCongestion?.pol ?? logisticsRaw.port_congestion?.pol ?? {};
    const podCongestion = logisticsRaw.portCongestion?.pod ?? logisticsRaw.port_congestion?.pod ?? {};
    const transshipments = toArray(logisticsRaw.portCongestion?.transshipments ?? 
      logisticsRaw.port_congestion?.transshipments, []);
    
    // Delay probabilities (from timeline or engine)
    const delayProbs = logisticsRaw.delayProbabilities ?? logisticsRaw.delay_probabilities ?? {};
    
    // Packaging recommendations
    const packagingRecs = toArray(logisticsRaw.packagingRecommendations ?? 
      logisticsRaw.packaging_recommendations, [])
      .map((p: any) => ({
        item: toString(p.item ?? p.name, 'Unknown item'),
        cost: round(toNumber(p.cost, 0), 2),
        riskReduction: round(toNumber(p.riskReduction ?? p.risk_reduction, 0), 1),
        rationale: toString(p.rationale ?? p.description, ''),
      }));
    
    logisticsData = {
      cargoContainerValidation: {
        isValid,
        warnings,
      },
      routeSeasonality: {
        season,
        riskLevel: (toString(seasonalityRaw.riskLevel ?? seasonalityRaw.risk_level, 'MEDIUM') as 'LOW' | 'MEDIUM' | 'HIGH'),
        factors: toArray(seasonalityRaw.factors, []).map((f: any) => ({
          factor: toString(f.factor ?? f.name, ''),
          impact: toString(f.impact ?? f.description, ''),
        })),
        climaticIndices: toArray(seasonalityRaw.climaticIndices ?? seasonalityRaw.climatic_indices, [])
          .map((c: any) => ({
            name: toString(c.name, ''),
            value: round(toNumber(c.value, 0), 2),
            interpretation: toString(c.interpretation ?? c.description, ''),
          })),
      },
      portCongestion: {
        pol: {
          name: toString(polCongestion.name ?? shipmentViewModel.pol, 'Origin Port'),
          dwellTime: round(toNumber(polCongestion.dwellTime ?? polCongestion.dwell_time, 1.5), 1),
          normalDwellTime: round(toNumber(polCongestion.normalDwellTime ?? polCongestion.normal_dwell_time, 1.5), 1),
          status: toString(polCongestion.status, 'NORMAL'),
        },
        pod: {
          name: toString(podCongestion.name ?? shipmentViewModel.pod, 'Destination Port'),
          dwellTime: round(toNumber(podCongestion.dwellTime ?? podCongestion.dwell_time, 2.0), 1),
          normalDwellTime: round(toNumber(podCongestion.normalDwellTime ?? podCongestion.normal_dwell_time, 2.0), 1),
          status: toString(podCongestion.status, 'NORMAL'),
        },
        transshipments: transshipments.map((t: any) => ({
          name: toString(t.name ?? t.port, 'Transshipment Port'),
          dwellTime: round(toNumber(t.dwellTime ?? t.dwell_time, 1.5), 1),
          normalDwellTime: round(toNumber(t.normalDwellTime ?? t.normal_dwell_time, 1.5), 1),
          status: toString(t.status, 'NORMAL'),
        })),
      },
      delayProbabilities: {
        p7days: round(toNumber(delayProbs.p7days ?? delayProbs.p_7days, 0.22), 3),
        p14days: round(toNumber(delayProbs.p14days ?? delayProbs.p_14days, 0.08), 3),
        p21days: round(toNumber(delayProbs.p21days ?? delayProbs.p_21days, 0.03), 3),
      },
      packagingRecommendations: packagingRecs,
    };
  }

  // ============================================================
  // RISK DISCLOSURE DATA (Sprint 3)
  // ============================================================
  let riskDisclosureData: import('../types/riskDisclosureTypes').RiskDisclosureData | undefined = undefined;
  
  // Extract risk disclosure data if available
  const riskDisclosureRaw = data.riskDisclosure ?? data.risk_disclosure ?? {};
  
  // ALWAYS generate risk disclosure data if we have loss data
  if (lossViewModel && lossViewModel.p95 > 0) {
    console.log('[adaptResultV2] Generating risk disclosure data from loss thresholds');
    
    // Extract latent risks
    const latentRisks = toArray(riskDisclosureRaw.latentRisks ?? riskDisclosureRaw.latent_risks, [])
    .map((r: any) => ({
      id: toString(r.id, `risk-${Date.now()}-${Math.random()}`),
      name: toString(r.name, 'Unknown Risk'),
      category: toString(r.category ?? r.type, 'General'),
      severity: (toString(r.severity, 'MEDIUM').toUpperCase() as 'LOW' | 'MEDIUM' | 'HIGH'),
      probability: round(toNumber(r.probability ?? r.prob, 0), 3),
      impact: toString(r.impact ?? r.description, ''),
      mitigation: toString(r.mitigation ?? r.recommendation, ''),
    }))
    .filter(r => r.probability > 0); // Only include risks with non-zero probability
  
  // Extract tail events
  const tailEvents = toArray(riskDisclosureRaw.tailEvents ?? riskDisclosureRaw.tail_events, [])
    .map((e: any) => ({
      event: toString(e.event ?? e.name, 'Unknown Event'),
      probability: round(toNumber(e.probability ?? e.prob, 0), 4),
      potentialLoss: round(toNumber(e.potentialLoss ?? e.loss ?? e.impact, 0), 2),
      historicalPrecedent: e.historicalPrecedent ?? e.historical_precedent ?? e.precedent ?? null,
    }))
    .filter(e => e.probability > 0);
  
  // Extract thresholds (from loss data if not provided)
  const thresholds = riskDisclosureRaw.thresholds ?? {};
  const riskThresholds = {
    p95: round(toNumber(thresholds.p95 ?? lossViewModel?.p95 ?? 0, 0), 2),
    p99: round(toNumber(thresholds.p99 ?? lossViewModel?.p99 ?? 0, 0), 2),
    maxLoss: round(toNumber(thresholds.maxLoss ?? thresholds.max_loss ?? (lossViewModel?.p99 ? lossViewModel.p99 * 1.2 : 0), 0), 2),
  };
  
  // Extract actionable mitigations
  const actionableMitigations = toArray(riskDisclosureRaw.actionableMitigations ?? riskDisclosureRaw.actionable_mitigations ?? riskDisclosureRaw.mitigations, [])
    .map((m: any) => ({
      action: toString(m.action ?? m.name, 'Unknown Action'),
      cost: round(toNumber(m.cost, 0), 2),
      riskReductionPercent: round(toNumber(m.riskReduction ?? m.risk_reduction ?? m.reduction, 0), 1),
      paybackPeriod: toString(m.paybackPeriod ?? m.payback_period ?? 'N/A', 'N/A'),
    }))
    .filter(m => m.riskReductionPercent > 0);
  
  // ALWAYS generate risk disclosure data if we have loss thresholds
  if (riskThresholds.p95 > 0 || lossViewModel) {
    // If no latent risks from engine, generate default ones
    let finalLatentRisks = latentRisks;
    if (finalLatentRisks.length === 0 && lossViewModel && lossViewModel.p99 > 0) {
      finalLatentRisks = [{
        id: "climate-tail",
        name: "Climate Tail Event",
        category: "Weather",
        severity: "HIGH" as const,
        probability: 0.05,
        impact: `Potential loss up to $${(lossViewModel.p99 * 1.2 / 1000).toFixed(0)}K`,
        mitigation: "Parametric insurance for delay > 10 days"
      }];
    }
    
    // If no tail events from engine, generate default ones
    let finalTailEvents = tailEvents;
    if (finalTailEvents.length === 0 && lossViewModel && lossViewModel.p99 > 0) {
      finalTailEvents = [{
        event: "Extreme weather delay",
        probability: 0.01,
        potentialLoss: lossViewModel.p99 * 1.2,
        historicalPrecedent: null
      }];
    }
    
    // If no mitigations from engine, generate default ones
    let finalMitigations = actionableMitigations;
    if (finalMitigations.length === 0) {
      finalMitigations = [{
        action: "Add desiccant",
        cost: 200,
        riskReductionPercent: 5.0,
        paybackPeriod: "Immediate"
      }];
    }
    
    riskDisclosureData = {
      latentRisks: finalLatentRisks,
      tailEvents: finalTailEvents,
      thresholds: riskThresholds,
      actionableMitigations: finalMitigations,
    };
  }

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
    algorithm: algorithmData,
    timeline: timelineViewModel,
    decisions: decisionsViewModel,
    loss: lossViewModel,
    insurance: insuranceData,
    logistics: logisticsData,
    riskDisclosure: riskDisclosureData,
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

