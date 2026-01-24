/**
 * Engine Response Schema Validation (Phase 3)
 * 
 * CRITICAL: This validates raw engine output BEFORE adaptation.
 * - Ensures data integrity from backend
 * - Reports missing/invalid fields
 * - Prevents fake data from entering the system
 * 
 * Rules:
 * - Never generate fake data - return validation errors instead
 * - Log warnings for recoverable issues (missing optional fields)
 * - Adapter handles all field normalization and type coercion
 */

// ============================================================================
// VALIDATION TYPES
// ============================================================================

/** Engine response is loosely typed - adapter handles normalization */
export type EngineResponse = Record<string, unknown>;

export interface ValidationResult {
  success: boolean;
  data: EngineResponse | null;
  errors: string[];
  warnings: string[];
  /** Is this from a mock/fake source? */
  isMock: boolean;
}

// ============================================================================
// VALIDATION FUNCTION
// ============================================================================

/**
 * Validate raw engine response
 * 
 * Simple validation that checks:
 * 1. Data is an object (not null/undefined/primitive)
 * 2. Data is not from mock source
 * 3. Reports warnings for missing fields
 * 
 * @param rawData - Raw data from engine API
 * @returns ValidationResult with data or errors
 */
export function validateEngineResponse(rawData: unknown): ValidationResult {
  const warnings: string[] = [];
  
  // Check for null/undefined
  if (rawData === null || rawData === undefined) {
    return {
      success: false,
      data: null,
      errors: ['Engine response is null or undefined'],
      warnings: [],
      isMock: false,
    };
  }
  
  // Check for non-object
  if (typeof rawData !== 'object') {
    return {
      success: false,
      data: null,
      errors: [`Engine response must be an object, got ${typeof rawData}`],
      warnings: [],
      isMock: false,
    };
  }
  
  const data = rawData as Record<string, unknown>;
  
  // Check for mock data indicators
  const engineVersion = data.engine_version ?? data.engineVersion;
  const isMock = 
    (typeof engineVersion === 'string' && engineVersion.includes('mock')) ||
    data._source === 'mock' ||
    data._synthetic === true;
  
  if (isMock) {
    console.warn('[validateEngineResponse] CRITICAL: Mock data detected - rejecting');
    return {
      success: false,
      data: null,
      errors: ['Mock/synthetic data detected - real engine data required'],
      warnings: [],
      isMock: true,
    };
  }
  
  // Check for required data presence (simple checks)
  const profile = data.profile as Record<string, unknown> | undefined;
  const layers = data.layers;
  
  // Must have at least one risk score source
  const hasRiskScore = 
    data.risk_score !== undefined ||
    data.overall_risk !== undefined ||
    data.riskScore !== undefined ||
    profile?.score !== undefined;
  
  if (!hasRiskScore) {
    warnings.push('No risk score found in response - will use default');
  }
  
  // Should have layers for breakdown
  if (!Array.isArray(layers) || layers.length === 0) {
    warnings.push('No layers found - breakdown will be empty');
  }
  
  // Should have shipment info
  if (!data.shipment) {
    warnings.push('No shipment data found - using defaults');
  }
  
  // Log warnings
  if (warnings.length > 0) {
    console.warn('[validateEngineResponse] Warnings:', warnings);
  }
  
  return {
    success: true,
    data: data as EngineResponse,
    errors: [],
    warnings,
    isMock: false,
  };
}

/**
 * Check if data is complete enough for full display
 * 
 * @param data - Validated engine data (any object)
 * @returns Object with completeness flags
 */
export function checkDataCompleteness(data: EngineResponse): {
  hasRiskScore: boolean;
  hasLayers: boolean;
  hasDrivers: boolean;
  hasLoss: boolean;
  hasDecisions: boolean;
  hasTimeline: boolean;
  completenessScore: number;
} {
  // Safe access using type assertion
  const d = data as Record<string, unknown>;
  const profile = d.profile as Record<string, unknown> | undefined;
  const timeline = d.timeline as Record<string, unknown> | undefined;
  
  const hasRiskScore = 
    d.risk_score !== undefined ||
    d.overall_risk !== undefined ||
    profile?.score !== undefined;
  
  const layers = d.layers;
  const hasLayers = Array.isArray(layers) && layers.length > 0;
  
  const drivers = d.drivers;
  const riskFactors = d.risk_factors;
  const factors = d.factors;
  const hasDrivers = 
    (Array.isArray(drivers) && drivers.length > 0) ||
    (Array.isArray(riskFactors) && riskFactors.length > 0) ||
    (Array.isArray(factors) && factors.length > 0);
  
  const hasLoss = 
    d.loss !== undefined ||
    d.financial !== undefined;
  
  const hasDecisions = 
    d.decision_summary !== undefined ||
    d.decisionSummary !== undefined;
  
  const projections = timeline?.projections;
  const scenarioProjections = d.riskScenarioProjections;
  const hasTimeline = 
    (Array.isArray(projections) && projections.length > 0) ||
    (Array.isArray(scenarioProjections) && scenarioProjections.length > 0);
  
  // Calculate completeness score (0-100)
  const flags = [hasRiskScore, hasLayers, hasDrivers, hasLoss, hasDecisions, hasTimeline];
  const completenessScore = Math.round((flags.filter(Boolean).length / flags.length) * 100);
  
  return {
    hasRiskScore,
    hasLayers,
    hasDrivers,
    hasLoss,
    hasDecisions,
    hasTimeline,
    completenessScore,
  };
}
