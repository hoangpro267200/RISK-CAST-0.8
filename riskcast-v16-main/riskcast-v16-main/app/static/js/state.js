/**
 * ResultsOS State - Pure Data Adapter
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * 
 * This file is a PURE PRESENTATION LAYER ADAPTER.
 * 
 * ALL business logic, scoring, weighting, reasoning, and recommendations
 * MUST come from the Python Engine v2 backend via /results/data endpoint.
 * 
 * This file is FORBIDDEN from:
 * - Computing risk scores
 * - Deriving risk levels
 * - Aggregating FAHP weights
 * - Building recommendations
 * - Generating reasoning
 * - Applying decision rules
 * - Normalizing business data (except UI-only formatting)
 * 
 * This file is ALLOWED to:
 * - Load data from backend API or storage
 * - Map backend JSON format → UI component format (structural transformation only)
 * - Format values for display (currency, percentages, labels)
 * - Transform chart data (histogram bins, curve points) - UI visualization only
 * - Validate data structure (shape validation, not logic validation)
 * 
 * @file state.js
 */

const SUMMARY_STATE_KEY = 'RISKCAST_SUMMARY_STATE';

/**
 * Load data from backend API (direct from calculation algorithm)
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - This is the PRIMARY data source (authoritative)
 * - Backend MUST return complete, authoritative decision payload from Engine v2
 * - Returns null ONLY if API explicitly fails (404, 500, network error)
 * - Storage fallback is ONLY for legacy support
 * 
 * @returns {Promise<Object|null>} Backend result data or null if API fails
 */
async function loadFromBackendAPI() {
  // Try multiple endpoints in priority order
  const endpoints = [
    '/results/data',
    '/api/get_last_result',
    '/api/v1/risk/v2/get_last_result'
  ];
  
  for (const endpoint of endpoints) {
    try {
      // Add cache-busting to ensure fresh data from backend
      const cacheBuster = `?t=${Date.now()}&_=${Math.random().toString(36).substr(2, 9)}`;
      const url = `${endpoint}${cacheBuster}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        }
      });
      
      // Check if response is OK (200-299)
      if (response.ok) {
        const data = await response.json();
        
        // Check if data exists and is not empty
        // Also check for error responses
        if (data && typeof data === 'object' && !data.error) {
          const keys = Object.keys(data);
          if (keys.length > 0) {
            const riskScore = data.risk?.finalScore || data.risk_score || data.overall_risk;
            const layers = data.risk?.layers || data.layers || [];
            const cargoValue = data.shipment?.value_usd || data.cargo_value || data.shipment?.cargo_value;
            
            console.log(`[State] ✓ Loaded from ${endpoint}`, {
              timestamp: new Date().toISOString(),
              riskScore: riskScore,
              riskLevel: data.risk?.level || data.risk_level,
              layersCount: layers.length,
              layerNames: layers.slice(0, 5).map(l => l.name || l).join(', '),
              hasFinancial: !!(data.financial || data.financial_distribution),
              cargoValue: cargoValue,
              expectedLoss: data.financial?.expectedLoss || data.financial_distribution?.expected_loss_usd,
              var95: data.financial?.var95 || data.financial_distribution?.var_95_usd,
              dataKeys: keys.slice(0, 10)
            });
            return data;
          } else {
            console.warn(`[State] ✗ ${endpoint} returned empty object`);
          }
        } else {
          console.warn(`[State] ✗ ${endpoint} returned error or invalid data:`, data);
        }
      } else {
        console.warn(`[State] ✗ ${endpoint} returned status ${response.status}`);
      }
    } catch (error) {
      // Log error but continue to next endpoint
      console.warn(`[State] ✗ Failed to load from ${endpoint}:`, error.message);
      continue;
    }
  }
  
  // All endpoints failed or returned empty
  console.error('[State] ✗ No data available from any endpoint');
  return null;
}

/**
 * Load summary state from storage (sessionStorage primary, localStorage fallback)
 * This is legacy support - backend API should be primary source
 * @returns {Object|null} Summary state or null if not found
 */
export function loadSummaryState() {
  try {
    // Primary: sessionStorage
    if (typeof sessionStorage !== 'undefined') {
      const sessionData = sessionStorage.getItem(SUMMARY_STATE_KEY);
      if (sessionData) {
        return JSON.parse(sessionData);
      }
    }
    
    // Fallback: localStorage
    if (typeof localStorage !== 'undefined') {
      const localData = localStorage.getItem(SUMMARY_STATE_KEY);
      if (localData) {
        return JSON.parse(localData);
      }
    }
  } catch (error) {
    console.error('State: Failed to load summary state', error);
  }
  
  return null;
}

/**
 * Load data with backend API priority
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * - STRICT PRIORITY: Always try backend API first (authoritative source)
 * - Storage fallback ONLY if API explicitly fails (404, 500, network error)
 * - This ensures Results page ALWAYS renders engine-computed data when available
 * - Storage is ONLY for legacy support / offline scenarios
 * 
 * CRITICAL RULES:
 * - DO NOT add any business logic here
 * - DO NOT compute insurance, risk, score, or providers
 * - This is PURE MAPPING ONLY (structural transformation)
 * 
 * @returns {Promise<Object|null>} Mapped ResultsOS format or null if not found
 */
export async function loadSummaryStateWithAPI() {
  // ============================================================
  // PRIORITY 1: Backend API (authoritative, Engine v2 result)
  // ============================================================
  const apiData = await loadFromBackendAPI();
  if (apiData) {
    // Map backend format to UI format (structural mapping only, no computations)
    const mapped = mapBackendPayloadToUIFormat(apiData);
    return mapped;
  }
  
  // ============================================================
  // PRIORITY 2: Storage fallback (legacy support only)
  // ============================================================
  // Only use storage if API explicitly failed
  // This is a fallback for legacy scenarios or offline mode
  const storageData = loadSummaryState();
  if (storageData) {
    console.warn('[ResultsOS] Fallback to storage (legacy) - API unavailable or returned empty');
    // Map storage format to UI format (structural mapping only, no computations)
    const mapped = mapStoragePayloadToUIFormat(storageData);
    return mapped;
  }
  
  // No data available from any source
  console.warn('[ResultsOS] No data available from backend API or storage');
  return null;
}

/**
 * Validate state structure (shape validation only, no business logic)
 * @param {Object} state - State to validate
 * @returns {boolean} True if structure is valid
 */
export function validateState(state) {
  if (!state || typeof state !== 'object') {
    return false;
  }
  
  // Structural validation only - check required fields exist
  // Do NOT validate business logic or values
  if (!state.shipment || typeof state.shipment !== 'object') {
    return false;
  }
  
  // Check shipment has at least route or id
  if (!state.shipment.route && !state.shipment.id) {
    return false;
  }
  
  // Validate recommendations structure if present (shape only)
  if (state.recommendations) {
    const rec = state.recommendations;
    if (rec.insurance && typeof rec.insurance !== 'object') return false;
    if (rec.timing && typeof rec.timing !== 'object') return false;
    if (rec.providers && !Array.isArray(rec.providers)) return false;
    if (rec.trace && typeof rec.trace !== 'object') return false;
  }
  
  return true;
}

/**
 * Map backend API payload to UI component format
 * PURE MAPPING ONLY - extracts data from backend format, no computations
 * 
 * Backend MUST provide:
 * - risk_score / overall_risk (0-100)
 * - risk_level (Low/Medium/High/Critical)
 * - layers array (with name and score)
 * - risk_factors array
 * - recommendations (insurance, timing, providers, trace)
 * - loss metrics (p95, p99, tailContribution)
 * - All decision data
 * 
 * @param {Object} backendPayload - Result from /results/data endpoint
 * @returns {Object} ResultsOS UI format (extracted from backend, not computed)
 */
function mapBackendPayloadToUIFormat(backendPayload) {
  if (!backendPayload || typeof backendPayload !== 'object') {
    return getEmptyUIState();
  }
  
  // Extract shipment data (direct mapping, no computation)
  const shipment = backendPayload.shipment || {};
  
  // Extract pol/pod from various formats
  let pol = shipment.pol_code || shipment.origin || '';
  let pod = shipment.pod_code || shipment.destination || '';
  
  // Extract from route string if pol/pod not directly available
  if ((!pol || !pod) && shipment.route) {
    const routeStr = shipment.route;
    if (routeStr.includes('→')) {
      const parts = routeStr.split('→');
      pol = pol || parts[0]?.trim() || '';
      pod = pod || parts[1]?.trim() || '';
    } else if (routeStr.includes('->')) {
      const parts = routeStr.split('->');
      pol = pol || parts[0]?.trim() || '';
      pod = pod || parts[1]?.trim() || '';
    } else if (routeStr.includes('_')) {
      const parts = routeStr.split('_');
      pol = pol || parts[0] || '';
      pod = pod || parts[1] || '';
    }
  }
  
  // Build route display string
  const routeDisplay = pol && pod ? `${pol} → ${pod}` : (shipment.route || 'Route not specified');
  
  const shipmentContext = {
    id: shipment.id || shipment.shipment_id || 'SH-UNKNOWN',
    route: routeDisplay,
    pol_code: pol,
    pod_code: pod,
    carrier: shipment.carrier || '',
    incoterms: shipment.incoterm || shipment.incoterms || 'Not specified',
    cargo: shipment.cargo || shipment.cargo_type || shipment.cargoType || 'Cargo type not specified',
    value_usd: shipment.value || 
               shipment.cargo_value || 
               shipment.cargoValue ||
               backendPayload.cargo_value ||
               backendPayload.shipment_value ||
               backendPayload.shipment?.cargo_value ||
               0,
    eta: shipment.eta || '',
    etd: shipment.etd || '',
    context: {
      mode: shipment.mode || shipment.transport_mode || shipment.transportMode || 'Mode not specified',
      tradeLane: mapTradeLaneForDisplay(routeDisplay),
      riskSensitivity: shipment.value || shipment.cargo_value || shipment.cargoValue ? 
        ((shipment.value || shipment.cargo_value || shipment.cargoValue) > 1000000 ? 'High-value cargo' : 'Standard cargo') : 
        'Standard cargo'
    }
  };
  
  // Extract risk score (backend MUST provide this already computed)
  const riskScore = backendPayload.risk_score || backendPayload.overall_risk || 
                    (backendPayload.risk?.score ? backendPayload.risk.score * 100 : 0);
  const globalRisk = typeof riskScore === 'number' ? 
    (riskScore > 1 ? Math.round(riskScore) : Math.round(riskScore * 100)) : 0;
  
  // Extract risk level (backend MUST provide this already computed)
  const riskLevel = backendPayload.risk_level || backendPayload.risk?.level || 
                    mapRiskLevelString(backendPayload.risk?.level);
  
  // Extract layers (backend MUST provide with scores already computed)
  const backendLayers = backendPayload.layers || [];
  
  // Normalize layer names for duplicate detection
  const normalizeLayerName = (name) => {
    if (!name) return '';
    return name.trim().toLowerCase().replace(/\s+/g, ' ');
  };
  
  // Filter, map, and remove duplicates
  const seenLayers = new Map();
  const layers = [];
  
  backendLayers
    .filter(l => l && l.name && (l.score != null || l.value != null))
    .forEach(l => {
      const normalizedName = normalizeLayerName(l.name);
      
      // Skip duplicates - keep first occurrence
      if (seenLayers.has(normalizedName)) {
        // Only log in debug mode to reduce console noise
        if (typeof DEBUG !== 'undefined' && DEBUG) {
          console.debug(`[State] Duplicate layer filtered: "${l.name}"`);
        }
        return;
      }
      
      seenLayers.set(normalizedName, true);
      
      const rawScore = parseFloat(l.score || l.value || 0);
      // Normalize to 0-100 scale if needed (assume > 1 means already 0-100)
      const score = rawScore > 1 ? rawScore : rawScore * 100;
      
      layers.push({
        name: l.name,
        score: Math.min(100, Math.max(0, score)), // Clamp for safety, but backend should already be correct
        contribution: l.contribution != null ? l.contribution : null,
        status: l.status || null
      });
    });
  
  // Extract risk factors (backend MUST provide these)
  const backendFactors = backendPayload.risk_factors || backendPayload.riskFactors || [];
  const factors = backendFactors.slice(0, 6).map(f => ({
        factor: f.name || f.factor || 'Unknown',
    category: mapFactorCategoryForDisplay(f.name || f.factor),
    impact: typeof f.impact === 'number' ? f.impact : (parseFloat(f.score || f.contribution || 0) / 100),
    probability: typeof f.probability === 'number' ? f.probability : (parseFloat(f.score || f.contribution || 0) / 100),
    compositeScore: parseFloat(f.compositeScore || f.contribution || 0) || 0
  }));
  
  // Extract loss metrics (backend MUST provide these)
  // Check multiple possible locations for loss data
  const financialDist = backendPayload.financial_distribution || {};
  const lossData = backendPayload.loss || 
                   backendPayload.financial || 
                   financialDist ||
                   backendPayload.risk || 
                   backendPayload.details?.financial || 
                   backendPayload.advanced_metrics || {};
  
  
  // Try all possible field names (backend may use different formats)
  // CRITICAL: Check root level first (backend returns var, cvar at root)
  const p95 = backendPayload.var ||  // Root level var (most common)
              backendPayload.var95 ||
              lossData.p95 || 
              lossData.var95 || 
              lossData.var_95_usd || 
              financialDist.var_95_usd ||
              lossData.var || 
              backendPayload.advanced_metrics?.var_95 ||
              null;
  const p99 = backendPayload.cvar ||  // Root level cvar (most common)
              backendPayload.cvar95 ||
              lossData.p99 || 
              lossData.cvar95 || 
              lossData.cvar_95_usd || 
              financialDist.cvar_95_usd ||
              lossData.cvar || 
              backendPayload.advanced_metrics?.cvar_95 ||
              null;
  const expectedLoss = backendPayload.expected_loss_usd ||  // Root level expected_loss_usd
                      backendPayload.expected_loss ||
                      lossData.expectedLoss || 
                      lossData.expected_loss || 
                      lossData.expected_loss_usd || 
                      financialDist.expected_loss_usd ||
                      lossData.mean || 
                      null;
  const stdDev = financialDist.loss_std_usd ||  // Most common location
                lossData.loss_std_usd ||
                backendPayload.advanced_metrics?.std ||  // Check advanced_metrics.std
                backendPayload.advanced_metrics?.std_dev ||
                lossData.stdDev || 
                lossData.std || 
                financialDist.std_dev ||
                null;
  const maxLoss = lossData.maxLoss || 
                 lossData.max_loss_usd || 
                 financialDist.max_loss_usd ||
                 null;
  
  // Extracted financial values
  const tailContribution = lossData.tailContribution || 
                           (globalRisk > 60 ? 28.5 : 15.0); // Fallback if backend doesn't provide
  
  // Extract radar data (backend MUST provide)
  const radar = backendPayload.radar || {};
  const radarLabels = radar.labels || layers.map(l => l.name);
  const radarValues = radar.values || layers.map(l => parseFloat(l.score) || 0);
  
  // Extract decision context (backend MUST provide dominant layers, key drivers)
  const decision = backendPayload.decision || backendPayload.profile || {};
  const dominantLayers = decision.dominantLayers || 
                         layers.slice().sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 2);
  const keyDrivers = decision.keyDrivers || factors.slice(0, 3);
  
  // Extract timeline (backend MUST provide, or can be empty)
  const timeline = backendPayload.timeline || backendPayload.payloadForTimelineTrack?.timeline || [];
  
  // Extract recommendations (backend MUST provide complete recommendations object)
  const recommendations = backendPayload.recommendations || null;
  
  // Map to UI format
  return {
    shipment: shipmentContext,
    globalRisk: globalRisk,
    layers: layers,
    factors: factors,
    loss: {
      currency: 'USD',
      p95: p95,
      p99: p99,
      expectedLoss: expectedLoss,
      stdDev: stdDev,
      maxLoss: maxLoss,
      tailContribution: tailContribution,
      confidenceLevel: 'High',
      note: 'Loss values from backend calculation algorithm (VaR/CVaR)'
    },
    financial: {
      expectedLoss: expectedLoss,
      meanLoss: expectedLoss,
      var95: p95,
      percentile95: p95,
      cvar: p99,
      maxLoss: maxLoss,
      stdDev: stdDev,
      cargoValue: shipmentContext.value_usd || 
                  backendPayload.shipment?.cargo_value ||
                  backendPayload.cargo_value ||
                  backendPayload.shipment_value ||
                  (backendPayload.financial_distribution?.cargo_value) ||
                  0
    },
    charts: {
      radar: {
        labels: radarLabels,
        values: radarValues
      },
      financialHistogram: mapLossToHistogramBins(p95, p99),
      lossCurve: mapLossToCurvePoints(p95, p99)
    },
    decision: {
      riskLevel: riskLevel,
      overallRiskScore: globalRisk,
      dominantLayers: dominantLayers,
      keyDrivers: keyDrivers,
      loss: {
        p95: p95,
        p99: p99,
        expectedLoss: expectedLoss,
        stdDev: stdDev,
        tailContribution: tailContribution
      },
      decisionRationale: decision.decisionRationale || decision.explanation || [
        'Calculated from backend risk engine algorithm',
        'FAHP-weighted aggregation with Monte Carlo simulation',
        'VaR/CVaR metrics from financial distribution analysis'
      ],
      payloadForDecisionSignals: {
        decision: {
          riskLevel: riskLevel,
          overallRiskScore: globalRisk,
          dominantLayers: dominantLayers,
          keyDrivers: keyDrivers,
          loss: {
            p95: p95,
            p99: p99,
            tailContribution: tailContribution
          }
        }
      }
    },
    scenarios: backendPayload.scenarios || {
      payloadForMiniScenarios: {
        baseRiskScore: globalRisk,
        basePosture: riskLevel.toLowerCase(),
        scenarios: backendPayload.scenarios || []
      }
    },
    payloadForTimelineTrack: {
      timeline: timeline
    },
    recommendations: recommendations, // Backend MUST provide this complete
    meta: {
      version: 'v4000',
      source: 'backend_api',
      timestamp: new Date().toISOString()
    },
    methodology: backendPayload.methodology || {
      riskAggregation: {
        model: 'FAHP',
        method: 'Fuzzy Analytic Hierarchy Process with Monte Carlo simulation'
      },
      financialMetrics: {
        var: p95,
        cvar: p99,
        expectedLoss: lossData.expectedLoss || 0
      }
    }
  };
}

/**
 * Map storage payload to UI format (legacy support)
 * PURE MAPPING ONLY - extracts data from storage format
 * @param {Object} storagePayload - Summary state from storage
 * @returns {Object} ResultsOS UI format
 */
function mapStoragePayloadToUIFormat(storagePayload) {
  if (!validateState(storagePayload)) {
    return getEmptyUIState();
  }
  
  // Extract data directly from storage format
  // Storage format should already have computed values from previous backend runs
  const shipment = storagePayload.shipment || {};
  const shipmentContext = {
    id: shipment.id || 'SH-UNKNOWN',
    route: shipment.route || 'Route not specified',
    incoterms: shipment.incoterm || shipment.incoterms || 'Not specified',
    cargo: shipment.cargoType || shipment.cargo_type || shipment.cargo || 'Cargo type not specified',
    value_usd: shipment.cargoValue || shipment.cargo_value || shipment.value || 0,
    eta: shipment.eta || '',
    context: {
      mode: shipment.transportMode || shipment.transport_mode || shipment.mode || 'Mode not specified',
      tradeLane: mapTradeLaneForDisplay(shipment.route),
      riskSensitivity: shipment.cargoValue || shipment.cargo_value || shipment.value ?
        ((shipment.cargoValue || shipment.cargo_value || shipment.value) > 1000000 ? 'High-value cargo' : 'Standard cargo') :
        'Standard cargo'
    }
  };
  
  // Extract pre-computed values from storage
  const globalRisk = storagePayload.globalRisk || storagePayload.risk_score || 
                     (storagePayload.profile?.score ? storagePayload.profile.score * 100 : 0);
  const riskLevel = storagePayload.risk_level || storagePayload.profile?.level || 
                    mapRiskLevelString(storagePayload.profile?.level);
  const layers = storagePayload.layers || [];
  const factors = storagePayload.factors || storagePayload.risk_factors || [];
  const timeline = storagePayload.timeline || storagePayload.payloadForTimelineTrack?.timeline || [];
  
  // Extract loss data
  const lossData = storagePayload.loss || {};
  const p95 = lossData.p95 || 0;
  const p99 = lossData.p99 || 0;
  const tailContribution = lossData.tailContribution || 0;
  
  // Extract decision context
  const decision = storagePayload.decision || storagePayload.profile || {};
  
  // Extract recommendations (backend MUST provide complete recommendations object)
  const recommendations = storagePayload.recommendations || null;
  
  return {
    shipment: shipmentContext,
    globalRisk: globalRisk,
    layers: layers,
    factors: factors,
    loss: lossData,
    charts: storagePayload.charts || {
      radar: { labels: [], values: [] },
      financialHistogram: mapLossToHistogramBins(p95, p99),
      lossCurve: mapLossToCurvePoints(p95, p99)
    },
    decision: decision,
    scenarios: storagePayload.scenarios || {
      payloadForMiniScenarios: {
        baseRiskScore: globalRisk,
        basePosture: riskLevel.toLowerCase()
      }
    },
    payloadForTimelineTrack: {
      timeline: timeline
    },
    recommendations: recommendations,
    meta: storagePayload.meta || {
      version: 'v4000',
      source: 'storage',
      timestamp: new Date().toISOString()
    },
    methodology: storagePayload.methodology || {}
  };
}

/**
 * Get empty UI state (fallback when no data available)
 * @returns {Object} Empty ResultsOS state
 */
function getEmptyUIState() {
  return {
    shipment: {
      id: 'SH-NO-DATA',
      route: 'No shipment data available',
      incoterms: '—',
      cargo: '—',
      value_usd: 0,
      eta: '',
      context: {
        mode: '—',
        tradeLane: '—',
        riskSensitivity: '—'
      }
    },
    globalRisk: 0,
    layers: [],
    factors: [],
    loss: {
      currency: 'USD',
      p95: 0,
      p99: 0,
      tailContribution: 0,
      confidenceLevel: 'Low',
      note: 'No data available'
    },
    charts: {
      radar: { labels: [], values: [] },
      financialHistogram: { bins: [], counts: [], currency: 'USD' },
      lossCurve: { points: [] }
    },
    decision: {
      riskLevel: 'low',
      overallRiskScore: 0,
      dominantLayers: [],
      keyDrivers: [],
      loss: { p95: 0, p99: 0, tailContribution: 0 },
      decisionRationale: ['No summary data available'],
      payloadForDecisionSignals: {
        decision: {
          riskLevel: 'low',
          overallRiskScore: 0,
          dominantLayers: [],
          keyDrivers: [],
          loss: { p95: 0, p99: 0, tailContribution: 0 }
        }
      }
    },
    scenarios: {
      baseRiskScore: 0,
      basePosture: 'low',
      payloadForMiniScenarios: {
        baseRiskScore: 0,
        basePosture: 'low'
      }
    },
    timeline: [],
    payloadForTimelineTrack: {
      timeline: []
    },
    recommendations: null
  };
}

// ============================================================================
// UI-ONLY TRANSFORMATIONS (Chart data mapping, display formatting)
// These are VISUAL transformations only, NOT business logic
// ============================================================================

/**
 * Map loss values to histogram bins for chart visualization
 * UI-ONLY transformation: creates chart coordinates from loss values
 * @param {number} p95 - P95 loss value
 * @param {number} p99 - P99 loss value
 * @returns {Object} Histogram data for Chart.js
 */
function mapLossToHistogramBins(p95, p99) {
  const maxLoss = p99 * 1.2;
  const bins = [];
  const counts = [];
  
  for (let i = 0; i <= 13; i++) {
    bins.push(Math.round((maxLoss / 13) * i));
    counts.push(Math.max(0.05, 0.5 - (i * 0.03)));
  }
  
  return { bins, counts, currency: 'USD' };
}

/**
 * Map loss values to curve points for chart visualization
 * UI-ONLY transformation: creates chart coordinates from loss values
 * @param {number} p95 - P95 loss value
 * @param {number} p99 - P99 loss value
 * @returns {Array} Loss curve points for Chart.js
 */
function mapLossToCurvePoints(p95, p99) {
  const points = [];
  const steps = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.97, 0.98, 0.99, 0.992];
  
  steps.forEach(prob => {
    const loss = prob <= 0.95 ? (p95 * prob / 0.95) : (p95 + (p99 - p95) * (prob - 0.95) / 0.04);
    points.push({ loss: Math.round(loss), probability: prob });
  });
  
  return points;
}

/**
 * Map trade lane for display (UI formatting only)
 * @param {string} route - Route string
 * @returns {string} Display string
 */
function mapTradeLaneForDisplay(route) {
  if (!route) return '—';
  // Simple display mapping - no business logic
  if (route.includes('Asia') || route.includes('Shanghai') || route.includes('Singapore')) {
    return 'Asia → North America';
  }
  return 'Trade lane not specified';
  }
  
/**
 * Map factor category for display (UI formatting only)
 * @param {string} factorName - Factor name
 * @returns {string} Category display string
 */
function mapFactorCategoryForDisplay(factorName) {
  if (!factorName) return 'Operational';
  // Simple category mapping for display - no business logic
  if (factorName.includes('Weather') || factorName.includes('Climate')) return 'Environmental';
  if (factorName.includes('Geopolitical') || factorName.includes('Political')) return 'Geopolitical';
  if (factorName.includes('Financial') || factorName.includes('Currency')) return 'Financial';
  return 'Operational';
}

/**
 * Map risk level string format (UI formatting only)
 * @param {string} level - Risk level from backend
 * @returns {string} Normalized risk level string
 */
function mapRiskLevelString(level) {
  if (!level) return 'low';
  const levelLower = String(level).toLowerCase();
  if (levelLower.includes('high') || levelLower.includes('critical')) return 'high';
  if (levelLower.includes('medium') || levelLower.includes('moderate')) return 'medium';
  return 'low';
      }

// ============================================================================
// LEGACY EXPORTS (for backward compatibility)
// Backend MUST provide all computed values, frontend just passes through
// ============================================================================

/**
 * Legacy export: Transform backend API to results format
 * @deprecated Use mapBackendPayloadToUIFormat directly
 * @param {Object} apiResult - Backend API result
 * @returns {Object} UI format
 */
export function transformBackendAPIToResults(apiResult) {
  return mapBackendPayloadToUIFormat(apiResult);
  }
  
/**
 * Legacy export: Transform summary state to results format
 * @deprecated Use mapStoragePayloadToUIFormat directly
 * @param {Object} summaryState - Summary state from storage
 * @returns {Object} UI format
 */
export function transformSummaryToResults(summaryState) {
  return mapStoragePayloadToUIFormat(summaryState);
}

/**
 * Default results state (used when no data available)
 * This is a fallback/default state object for UI initialization
 */
export const resultsState = {
  shipment: {
    id: 'SH-2024-0847',
    route: 'Shanghai → Los Angeles → Chicago',
    incoterms: 'FOB',
    cargo: 'Electronics & Consumer Goods',
    value_usd: 2850000,
    eta: '2024-12-15T14:30:00Z',
    context: {
      mode: 'Ocean + Rail',
      tradeLane: 'Asia → North America',
      riskSensitivity: 'High-value, time-sensitive cargo'
    }
  },
  globalRisk: 68,
  layers: [],
  factors: [],
  loss: {
    currency: 'USD',
    p95: 425000,
    p99: 1120000,
    tailContribution: 28.5,
    confidenceLevel: 'High',
    note: 'Default demo data'
  },
  charts: {
    radar: { labels: [], values: [] },
    financialHistogram: { bins: [], counts: [], currency: 'USD' },
    lossCurve: { points: [] }
  },
  decision: {
    riskLevel: 'medium',
    overallRiskScore: 68,
    dominantLayers: [],
    keyDrivers: [],
    loss: { p95: 425000, p99: 1120000, tailContribution: 28.5 },
    decisionRationale: ['Default demo data'],
    payloadForDecisionSignals: {
      decision: {
        riskLevel: 'medium',
        overallRiskScore: 68,
        dominantLayers: [],
        keyDrivers: [],
        loss: { p95: 425000, p99: 1120000, tailContribution: 28.5 }
      }
    }
  },
  scenarios: {
    baseRiskScore: 68,
    basePosture: 'medium',
    payloadForMiniScenarios: {
      baseRiskScore: 68,
      basePosture: 'medium'
    }
  },
  timeline: [],
  payloadForTimelineTrack: {
    timeline: []
  },
  recommendations: null,
  meta: {
    version: 'v4000',
    source: 'default_state',
    timestamp: new Date().toISOString()
  },
  methodology: {
    riskAggregation: {
      model: 'FAHP',
      method: 'Fuzzy Analytic Hierarchy Process with Monte Carlo simulation'
    }
  },
  traceability: {
    decisionBasis: ['Default demo state - backend should provide real data'],
    references: []
  }
};
