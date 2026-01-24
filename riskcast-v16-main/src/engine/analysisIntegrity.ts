/**
 * Analysis Integrity Layer
 * 
 * CRITICAL: Validates engine responses for truthfulness and usefulness
 * BEFORE the adapter transforms them into UI view models.
 * 
 * Three classes of checks:
 * 1. PROVENANCE - Confirms data is truly from analysis (not mock/stale)
 * 2. PROVENANCE MATCHING - Confirms response matches expected input context
 * 3. CONSISTENCY - Confirms data makes sense for analysis
 * 
 * This layer MUST run before any UI rendering decisions.
 */

// ============================================================================
// TYPES
// ============================================================================

export type IntegrityStatus = 'ok' | 'warning' | 'invalid';

export interface IntegrityIssue {
  code: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  affectedSections: string[];
}

export interface ProvenanceInfo {
  runId: string | null;
  requestId: string | null;
  engineVersion: string | null;
  analyzedAt: string | null;
  caseId: string | null;
  inputHash: string | null;
}

export interface SectionGating {
  showOverview: boolean;
  showRiskScore: boolean;
  showLossMetrics: boolean;
  showLossCharts: boolean;
  showDrivers: boolean;
  showLayers: boolean;
  showDecisions: boolean;
  showScenarios: boolean;
  showTimeline: boolean;
  showAlgorithm: boolean;
}

export interface IntegrityResult {
  status: IntegrityStatus;
  issues: IntegrityIssue[];
  gating: SectionGating;
  provenance: ProvenanceInfo;
  /** Raw data passed validation */
  isValid: boolean;
  /** Data is usable for display (may have warnings) */
  isUsable: boolean;
}

export interface ValidationContext {
  expectedCaseId?: string;
  expectedRunId?: string;
  expectedInputHash?: string;
  expectedCargoValue?: number;
  expectedCurrency?: string;
  expectedPol?: string;
  expectedPod?: string;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function isNumber(val: unknown): val is number {
  return typeof val === 'number' && !isNaN(val) && isFinite(val);
}

function isPositiveNumber(val: unknown): val is number {
  return isNumber(val) && val >= 0;
}

function isNonEmptyArray(val: unknown): val is unknown[] {
  return Array.isArray(val) && val.length > 0;
}

function isNonEmptyString(val: unknown): val is string {
  return typeof val === 'string' && val.trim().length > 0;
}

/**
 * Normalize loss metrics to explicit fields
 */
function normalizeLossMetrics(lossData: Record<string, unknown>): {
  expectedLoss: number | null;
  var95: number | null;
  cvar95: number | null;
  var99: number | null;
  cvar99: number | null;
} {
  // Extract from various possible field names
  const expectedLoss = lossData.expectedLoss ?? lossData.expected_loss ?? null;
  const p95 = lossData.p95 ?? lossData.var95 ?? lossData.var_95 ?? null;
  const p99 = lossData.p99 ?? lossData.var99 ?? lossData.var_99 ?? null;
  const cvar95 = lossData.cvar95 ?? lossData.cvar_95 ?? lossData.cVaR95 ?? null;
  const cvar99 = lossData.cvar99 ?? lossData.cvar_99 ?? lossData.cVaR99 ?? lossData.cvar ?? null;
  
  return {
    expectedLoss: isPositiveNumber(expectedLoss) ? expectedLoss : null,
    var95: isPositiveNumber(p95) ? p95 : null,
    cvar95: isPositiveNumber(cvar95) ? cvar95 : null,
    var99: isPositiveNumber(p99) ? p99 : null,
    cvar99: isPositiveNumber(cvar99) ? cvar99 : null,
  };
}

// ============================================================================
// PROVENANCE CHECKS
// ============================================================================

function checkProvenance(data: Record<string, unknown>): {
  provenance: ProvenanceInfo;
  issues: IntegrityIssue[];
} {
  const issues: IntegrityIssue[] = [];
  
  // Extract provenance fields - try multiple sources for each field
  const runId = data.run_id ?? data.runId ?? data.analysis_id ?? data.analysisId ?? 
                data.request_id ?? data.requestId ?? 
                (data.meta as Record<string, unknown>)?.runId ?? null;
  const requestId = data.request_id ?? data.requestId ?? null;
  const engineVersion = data.engine_version ?? data.engineVersion ?? null;
  const analyzedAt = data.timestamp ?? data.analyzed_at ?? data.analyzedAt ?? 
                     (data.meta as Record<string, unknown>)?.timestamp ?? null;
  const caseId = data.case_id ?? data.caseId ?? 
                 (data.shipment as Record<string, unknown>)?.id ?? 
                 (data.shipment as Record<string, unknown>)?.shipment_id ??
                 (data.meta as Record<string, unknown>)?.caseId ?? null;
  const inputHash = data.input_hash ?? data.inputHash ?? data.request_hash ?? data.requestHash ?? null;
  
  const provenance: ProvenanceInfo = {
    runId: isNonEmptyString(runId) ? runId : null,
    requestId: isNonEmptyString(requestId) ? requestId : null,
    engineVersion: isNonEmptyString(engineVersion) ? String(engineVersion) : null,
    analyzedAt: isNonEmptyString(analyzedAt) ? String(analyzedAt) : null,
    caseId: isNonEmptyString(caseId) ? String(caseId) : null,
    inputHash: isNonEmptyString(inputHash) ? String(inputHash) : null,
  };
  
  // HARDENED mock detection - treat ANY of these as INVALID
  const engineVersionStr = String(engineVersion ?? '').toLowerCase();
  const isMock = 
    engineVersionStr.includes('mock') ||
    engineVersionStr.includes('test') ||
    engineVersionStr.includes('fake') ||
    data._source === 'mock' ||
    data._synthetic === true ||
    data.is_mock === true ||
    data.isMock === true ||
    data._test === true ||
    data._fake === true;
  
  if (isMock) {
    issues.push({
      code: 'MOCK_DATA_DETECTED',
      severity: 'error',
      message: 'Analysis response contains mock/synthetic data indicators - REJECTED',
      affectedSections: ['all'],
    });
  }
  
  // Warn if no run ID (non-blocking - data can still be used)
  if (!provenance.runId) {
    issues.push({
      code: 'MISSING_RUN_ID',
      severity: 'info', // Downgraded to info - not critical for data display
      message: 'No run ID in response - provenance tracking limited',
      affectedSections: ['overview'],
    });
  }
  
  // Warn if no timestamp
  if (!provenance.analyzedAt) {
    issues.push({
      code: 'MISSING_TIMESTAMP',
      severity: 'info',
      message: 'No analysis timestamp in response',
      affectedSections: ['overview'],
    });
  }
  
  return { provenance, issues };
}

// ============================================================================
// PROVENANCE MATCHING CHECKS
// ============================================================================

/**
 * Extract numeric/timestamp part from case ID for flexible matching
 * Handles formats like: "CASE-1769074185194", "SH-VNSGN-CNSHA-1769074185", etc.
 * Also handles cases where timestamps might be truncated or different lengths
 */
function extractCaseIdNumeric(caseId: string): string | null {
  // Extract all digits from the end (timestamp-like part)
  const match = caseId.match(/\d+$/);
  if (match) {
    return match[0];
  }
  // If no trailing digits, try to extract any long numeric sequence
  const allDigits = caseId.replace(/\D/g, '');
  return allDigits.length >= 10 ? allDigits : null;
}

/**
 * Check if two case IDs are likely the same despite format differences
 * Allows for truncated timestamps or different prefixes
 */
function areCaseIdsCompatible(id1: string, id2: string): boolean {
  const num1 = extractCaseIdNumeric(id1);
  const num2 = extractCaseIdNumeric(id2);
  
  if (!num1 || !num2) {
    // If we can't extract numeric parts, fall back to exact match
    return id1 === id2;
  }
  
  // If numeric parts are the same, they're compatible
  if (num1 === num2) {
    return true;
  }
  
  // If one is a prefix of the other (handles truncated timestamps)
  // Allow if they match in the first 10 digits (timestamp precision)
  const minLength = Math.min(num1.length, num2.length);
  if (minLength >= 10) {
    return num1.substring(0, 10) === num2.substring(0, 10);
  }
  
  return false;
}

function checkProvenanceMatching(
  data: Record<string, unknown>,
  provenance: ProvenanceInfo,
  context: ValidationContext
): IntegrityIssue[] {
  const issues: IntegrityIssue[] = [];
  
  // Case ID mismatch - use flexible matching based on numeric/timestamp part
  if (context.expectedCaseId && provenance.caseId) {
    // Use compatible check which handles truncated timestamps
    if (!areCaseIdsCompatible(context.expectedCaseId, provenance.caseId)) {
      // Only warn if IDs are truly incompatible
      // Don't set affectedSections to 'all' - this is just a tracking issue
      issues.push({
        code: 'CASE_ID_MISMATCH',
        severity: 'info', // Downgraded to info - not critical
        message: `Response case ID (${provenance.caseId}) differs from expected (${context.expectedCaseId}) - using response ID`,
        affectedSections: [], // Don't affect any sections
      });
    }
    // If IDs are compatible (same timestamp), no issue
  }
  
  // Run ID mismatch
  if (context.expectedRunId && provenance.runId) {
    if (provenance.runId !== context.expectedRunId) {
      issues.push({
        code: 'RUN_ID_MISMATCH',
        severity: 'error',
        message: `Response run ID (${provenance.runId}) does not match expected (${context.expectedRunId})`,
        affectedSections: ['all'],
      });
    }
  }
  
  // Input hash mismatch (critical for stale data detection)
  if (context.expectedInputHash && provenance.inputHash) {
    if (provenance.inputHash !== context.expectedInputHash) {
      issues.push({
        code: 'INPUT_HASH_MISMATCH',
        severity: 'error',
        message: 'Response input hash does not match expected - this may be stale data from a different analysis',
        affectedSections: ['all'],
      });
    }
  }
  
  // Cargo value mismatch (material difference check)
  if (context.expectedCargoValue !== undefined && context.expectedCargoValue !== null) {
    const shipment = data.shipment as Record<string, unknown> | undefined;
    const responseCargoValue = 
      shipment?.cargo_value ?? 
      shipment?.cargoValue ?? 
      shipment?.value ??
      data.cargo_value ??
      data.cargoValue ??
      data.value;
    
    if (isNumber(responseCargoValue)) {
      // Allow 1% tolerance for rounding, but flag larger differences
      const diff = Math.abs(responseCargoValue - context.expectedCargoValue);
      const tolerance = Math.max(context.expectedCargoValue * 0.01, 100);
      
      if (diff > tolerance) {
        issues.push({
          code: 'CARGO_VALUE_MISMATCH',
          severity: 'error',
          message: `Response cargo value (${responseCargoValue}) differs significantly from expected (${context.expectedCargoValue})`,
          affectedSections: ['all'],
        });
      }
    }
  }
  
  // Currency mismatch
  if (context.expectedCurrency) {
    const shipment = data.shipment as Record<string, unknown> | undefined;
    const cargoValueObj = shipment?.cargoValue as Record<string, unknown> | undefined;
    const responseCurrency = 
      shipment?.currency ?? 
      cargoValueObj?.currency ??
      data.currency;
    
    if (isNonEmptyString(responseCurrency) && responseCurrency !== context.expectedCurrency) {
      issues.push({
        code: 'CURRENCY_MISMATCH',
        severity: 'error',
        message: `Response currency (${responseCurrency}) does not match expected (${context.expectedCurrency})`,
        affectedSections: ['lossMetrics', 'lossCharts'],
      });
    }
  }
  
  // Route mismatch (POL/POD)
  if (context.expectedPol || context.expectedPod) {
    const shipment = data.shipment as Record<string, unknown> | undefined;
    const responsePol = shipment?.pol ?? shipment?.pol_code ?? shipment?.origin;
    const responsePod = shipment?.pod ?? shipment?.pod_code ?? shipment?.destination;
    
    if (context.expectedPol && isNonEmptyString(responsePol) && responsePol !== context.expectedPol) {
      issues.push({
        code: 'POL_MISMATCH',
        severity: 'error',
        message: `Response POL (${responsePol}) does not match expected (${context.expectedPol})`,
        affectedSections: ['all'],
      });
    }
    
    if (context.expectedPod && isNonEmptyString(responsePod) && responsePod !== context.expectedPod) {
      issues.push({
        code: 'POD_MISMATCH',
        severity: 'error',
        message: `Response POD (${responsePod}) does not match expected (${context.expectedPod})`,
        affectedSections: ['all'],
      });
    }
  }
  
  return issues;
}

// ============================================================================
// CONSISTENCY CHECKS (with normalized loss metrics)
// ============================================================================

function checkConsistency(data: Record<string, unknown>): IntegrityIssue[] {
  const issues: IntegrityIssue[] = [];
  
  // Extract relevant fields
  const profile = data.profile as Record<string, unknown> | undefined;
  const loss = data.loss as Record<string, unknown> | undefined;
  const financial = data.financial as Record<string, unknown> | undefined;
  const lossData = loss ?? financial;
  
  // Risk score range check (0-100)
  const riskScore = profile?.score ?? data.risk_score ?? data.overall_risk ?? data.riskScore;
  if (isNumber(riskScore)) {
    if (riskScore < 0 || riskScore > 100) {
      issues.push({
        code: 'RISK_SCORE_OUT_OF_RANGE',
        severity: 'warning',
        message: `Risk score ${riskScore} is outside valid range [0, 100]`,
        affectedSections: ['overview', 'riskScore'],
      });
    }
  }
  
  // Confidence range check (0-1 or 0-100)
  const confidence = profile?.confidence ?? data.confidence;
  if (isNumber(confidence)) {
    // Normalize to 0-1 range for checking
    const normalizedConf = confidence > 1 ? confidence / 100 : confidence;
    if (normalizedConf < 0 || normalizedConf > 1) {
      issues.push({
        code: 'CONFIDENCE_OUT_OF_RANGE',
        severity: 'warning',
        message: `Confidence ${confidence} is outside valid range`,
        affectedSections: ['overview'],
      });
    }
  }
  
  // Loss metrics consistency with normalized fields
  if (lossData) {
    const metrics = normalizeLossMetrics(lossData);
    
    // Rule: expectedLoss <= var95 <= var99
    if (metrics.expectedLoss !== null && metrics.var95 !== null) {
      if (metrics.var95 < metrics.expectedLoss) {
        issues.push({
          code: 'VAR_LESS_THAN_EXPECTED_LOSS',
          severity: 'error',
          message: `VaR 95% (${metrics.var95}) cannot be less than Expected Loss (${metrics.expectedLoss})`,
          affectedSections: ['lossMetrics', 'lossCharts'],
        });
      }
    }
    
    if (metrics.var95 !== null && metrics.var99 !== null) {
      if (metrics.var99 < metrics.var95) {
        issues.push({
          code: 'VAR_QUANTILES_NOT_MONOTONIC',
          severity: 'error',
          message: `VaR 99% (${metrics.var99}) cannot be less than VaR 95% (${metrics.var95})`,
          affectedSections: ['lossMetrics', 'lossCharts'],
        });
      }
    }
    
    // Rule: cvar95 >= var95, cvar99 >= var99
    if (metrics.cvar95 !== null && metrics.var95 !== null) {
      if (metrics.cvar95 < metrics.var95) {
        issues.push({
          code: 'CVAR95_LESS_THAN_VAR95',
          severity: 'error',
          message: `CVaR 95% (${metrics.cvar95}) cannot be less than VaR 95% (${metrics.var95})`,
          affectedSections: ['lossMetrics', 'lossCharts'],
        });
      }
    }
    
    if (metrics.cvar99 !== null && metrics.var99 !== null) {
      if (metrics.cvar99 < metrics.var99) {
        issues.push({
          code: 'CVAR99_LESS_THAN_VAR99',
          severity: 'error',
          message: `CVaR 99% (${metrics.cvar99}) cannot be less than VaR 99% (${metrics.var99})`,
          affectedSections: ['lossMetrics', 'lossCharts'],
        });
      }
    }
    
    // All must be >= 0
    const allMetrics = [
      metrics.expectedLoss,
      metrics.var95,
      metrics.cvar95,
      metrics.var99,
      metrics.cvar99,
    ].filter((v): v is number => v !== null);
    
    for (const metric of allMetrics) {
      if (metric < 0) {
        issues.push({
          code: 'NEGATIVE_LOSS_METRIC',
          severity: 'error',
          message: `Loss metric cannot be negative: ${metric}`,
          affectedSections: ['lossMetrics', 'lossCharts'],
        });
      }
    }
  }
  
  // Layers validation
  const layers = data.layers as unknown[] | undefined;
  if (isNonEmptyArray(layers)) {
    // Check if layer contributions sum to reasonable range
    const totalContribution = layers.reduce((sum: number, layer: unknown) => {
      const contrib = (layer as Record<string, unknown>)?.contribution;
      return sum + (isNumber(contrib) ? contrib : 0);
    }, 0);
    
    if (totalContribution > 150) {
      issues.push({
        code: 'LAYER_CONTRIBUTIONS_EXCESSIVE',
        severity: 'warning',
        message: `Total layer contributions (${totalContribution}%) exceed expected range`,
        affectedSections: ['layers'],
      });
    }
  }
  
  // Drivers validation
  const drivers = data.drivers ?? data.risk_factors ?? data.factors;
  if (isNonEmptyArray(drivers)) {
    // Check for empty driver names
    const emptyDrivers = (drivers as Record<string, unknown>[]).filter(
      d => !isNonEmptyString(d.name) && !isNonEmptyString(d.label)
    );
    if (emptyDrivers.length > 0) {
      issues.push({
        code: 'EMPTY_DRIVER_NAMES',
        severity: 'warning',
        message: `${emptyDrivers.length} driver(s) have no name`,
        affectedSections: ['drivers'],
      });
    }
  }
  
  return issues;
}

// ============================================================================
// GATING LOGIC
// ============================================================================

function computeGating(
  data: Record<string, unknown>,
  issues: IntegrityIssue[]
): SectionGating {
  // Start with all sections enabled
  const gating: SectionGating = {
    showOverview: true,
    showRiskScore: true,
    showLossMetrics: true,
    showLossCharts: true,
    showDrivers: true,
    showLayers: true,
    showDecisions: true,
    showScenarios: true,
    showTimeline: true,
    showAlgorithm: true,
  };
  
  // If mock data detected, disable everything
  if (issues.some(i => i.code === 'MOCK_DATA_DETECTED')) {
    Object.keys(gating).forEach(k => ((gating as unknown) as Record<string, boolean>)[k] = false);
    return gating;
  }
  
  // If provenance mismatch, disable everything
  if (issues.some(i => 
    // Case ID mismatches are warnings and no longer treated as fatal
    i.code === 'RUN_ID_MISMATCH' || 
    i.code === 'INPUT_HASH_MISMATCH' ||
    i.code === 'CARGO_VALUE_MISMATCH'
  )) {
    Object.keys(gating).forEach(k => ((gating as unknown) as Record<string, boolean>)[k] = false);
    return gating;
  }
  
  // Check data availability for each section
  // CRITICAL: Only enable sections if real engine data exists
  // Do not enable based on defaults/placeholders
  const profile = data.profile as Record<string, unknown> | undefined;
  const loss = data.loss as Record<string, unknown> | undefined;
  const financial = data.financial as Record<string, unknown> | undefined;
  const lossData = loss ?? financial;
  
  // Risk score - must be a valid number > 0 or explicitly 0 (not default)
  const riskScore = profile?.score ?? data.risk_score ?? data.overall_risk ?? data.riskScore;
  const hasRiskScore = isNumber(riskScore) && riskScore >= 0 && riskScore <= 100;
  gating.showRiskScore = hasRiskScore;
  
  // Loss metrics (using normalized fields) - must have at least one metric
  if (lossData) {
    const metrics = normalizeLossMetrics(lossData);
    const hasLossMetrics = 
      metrics.expectedLoss !== null ||
      metrics.var95 !== null ||
      metrics.var99 !== null ||
      metrics.cvar95 !== null ||
      metrics.cvar99 !== null;
    gating.showLossMetrics = hasLossMetrics;
    
    // Loss charts (need loss curve or histogram data)
    // Also check for distribution_shapes.loss_histogram or loss_distribution array
    const hasLossCurve = isNonEmptyArray(lossData.lossCurve ?? lossData.loss_curve);
    const hasHistogram = isNonEmptyArray(lossData.histogram);
    const hasDistributionHistogram = isNonEmptyArray((data.distribution_shapes as Record<string, unknown>)?.loss_histogram);
    const hasDistributionArray = isNonEmptyArray(data.loss_distribution);
    gating.showLossCharts = hasLossCurve || hasHistogram || hasDistributionHistogram || hasDistributionArray;
  } else {
    gating.showLossMetrics = false;
    gating.showLossCharts = false;
  }
  
  // Drivers
  const drivers = data.drivers ?? data.risk_factors ?? data.factors;
  gating.showDrivers = isNonEmptyArray(drivers);
  
  // Layers
  gating.showLayers = isNonEmptyArray(data.layers);
  
  // Decisions
  const decisions = data.decision_summary ?? data.decisionSummary;
  gating.showDecisions = decisions !== undefined && decisions !== null;
  
  // Scenarios
  gating.showScenarios = isNonEmptyArray(data.scenarios);
  
  // Timeline
  const timeline = data.timeline as Record<string, unknown> | undefined;
  gating.showTimeline = 
    isNonEmptyArray(timeline?.projections) ||
    isNonEmptyArray(data.riskScenarioProjections);
  
  // Algorithm
  gating.showAlgorithm = data.algorithm !== undefined && data.algorithm !== null;
  
  // Overview requires at least risk score
  gating.showOverview = gating.showRiskScore;
  
  // Apply issue-based gating
  // CRITICAL: Only disable sections for actual errors, not warnings
  // Warnings should not block data display
  for (const issue of issues) {
    if (issue.severity === 'error') {
      // Only block on critical errors, not all errors
      const isCriticalError = 
        issue.code === 'MOCK_DATA_DETECTED' ||
        issue.code === 'INPUT_HASH_MISMATCH' ||
        issue.code === 'CARGO_VALUE_MISMATCH' ||
        issue.code === 'RUN_ID_MISMATCH';
      
      if (isCriticalError) {
        for (const section of issue.affectedSections) {
          if (section === 'all') {
            Object.keys(gating).forEach(k => ((gating as unknown) as Record<string, boolean>)[k] = false);
            break;
          }
          const key = `show${section.charAt(0).toUpperCase() + section.slice(1)}` as keyof SectionGating;
          if (key in gating) {
            gating[key] = false;
          }
        }
      }
      // Non-critical errors (like consistency errors) only affect specific sections
      else {
        for (const section of issue.affectedSections) {
          if (section !== 'all') {
            const key = `show${section.charAt(0).toUpperCase() + section.slice(1)}` as keyof SectionGating;
            if (key in gating) {
              gating[key] = false;
            }
          }
        }
      }
    }
    // Warnings and info issues should never disable sections
  }
  
  return gating;
}

// ============================================================================
// MAIN VALIDATION FUNCTION
// ============================================================================

/**
 * Validate analysis response for integrity before UI rendering
 * 
 * @param rawResponse - Raw engine response (unknown type)
 * @param context - Expected context for provenance matching (optional)
 * @returns IntegrityResult with status, issues, gating, and provenance
 */
export function validateAnalysisIntegrity(
  rawResponse: unknown,
  context: ValidationContext = {}
): IntegrityResult {
  // Default result for invalid input
  const invalidResult: IntegrityResult = {
    status: 'invalid',
    issues: [{
      code: 'INVALID_RESPONSE',
      severity: 'error',
      message: 'Analysis response is null, undefined, or not an object',
      affectedSections: ['all'],
    }],
    gating: {
      showOverview: false,
      showRiskScore: false,
      showLossMetrics: false,
      showLossCharts: false,
      showDrivers: false,
      showLayers: false,
      showDecisions: false,
      showScenarios: false,
      showTimeline: false,
      showAlgorithm: false,
    },
    provenance: {
      runId: null,
      requestId: null,
      engineVersion: null,
      analyzedAt: null,
      caseId: null,
      inputHash: null,
    },
    isValid: false,
    isUsable: false,
  };
  
  // Type guard
  if (rawResponse === null || rawResponse === undefined) {
    return invalidResult;
  }
  
  if (typeof rawResponse !== 'object') {
    return {
      ...invalidResult,
      issues: [{
        code: 'INVALID_RESPONSE_TYPE',
        severity: 'error',
        message: `Expected object, got ${typeof rawResponse}`,
        affectedSections: ['all'],
      }],
    };
  }
  
  const data = rawResponse as Record<string, unknown>;
  const allIssues: IntegrityIssue[] = [];
  
  // Run provenance checks
  const { provenance, issues: provenanceIssues } = checkProvenance(data);
  allIssues.push(...provenanceIssues);
  
  // Run provenance matching checks (if context provided)
  if (Object.keys(context).length > 0) {
    const matchingIssues = checkProvenanceMatching(data, provenance, context);
    allIssues.push(...matchingIssues);
  }
  
  // Run consistency checks
  const consistencyIssues = checkConsistency(data);
  allIssues.push(...consistencyIssues);
  
  // Compute gating
  const gating = computeGating(data, allIssues);
  
  // Determine overall status
  const hasErrors = allIssues.some(i => i.severity === 'error');
  const hasWarnings = allIssues.some(i => i.severity === 'warning');
  
  let status: IntegrityStatus = 'ok';
  if (hasErrors) {
    status = 'invalid';
  } else if (hasWarnings) {
    status = 'warning';
  }
  
  // Check if usable (at least overview can show)
  // More lenient: consider data usable if we have ANY meaningful data, even with warnings
  const isUsable = Boolean(
    gating.showOverview || gating.showRiskScore || 
    gating.showLayers || gating.showDrivers ||
    (data.shipment && Object.keys(data.shipment as Record<string, unknown>).length > 0)
  );
  
  return {
    status,
    issues: allIssues,
    gating,
    provenance,
    isValid: !hasErrors,
    isUsable,
  };
}

/**
 * Create a debug summary for development
 */
export function formatIntegrityDebug(result: IntegrityResult): string {
  const lines: string[] = [
    `=== Analysis Integrity Check ===`,
    `Status: ${result.status.toUpperCase()}`,
    `Valid: ${result.isValid}, Usable: ${result.isUsable}`,
    ``,
    `Provenance:`,
    `  Run ID: ${result.provenance.runId || 'N/A'}`,
    `  Engine: ${result.provenance.engineVersion || 'N/A'}`,
    `  Analyzed: ${result.provenance.analyzedAt || 'N/A'}`,
    `  Case ID: ${result.provenance.caseId || 'N/A'}`,
    `  Input Hash: ${result.provenance.inputHash || 'N/A'}`,
    ``,
    `Gating:`,
  ];
  
  for (const [key, value] of Object.entries(result.gating)) {
    lines.push(`  ${key}: ${value ? '✓' : '✗'}`);
  }
  
  if (result.issues.length > 0) {
    lines.push('');
    lines.push(`Issues (${result.issues.length}):`);
    for (const issue of result.issues) {
      lines.push(`  [${issue.severity.toUpperCase()}] ${issue.code}: ${issue.message}`);
    }
  }
  
  return lines.join('\n');
}
