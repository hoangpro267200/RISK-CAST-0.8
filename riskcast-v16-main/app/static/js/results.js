/**
 * ResultsOS Data Loading & Normalization
 * 
 * RESPONSIBILITIES:
 * - Load summary data from multiple sources (window, sessionStorage, API)
 * - Normalize different data formats to a consistent schema
 * - Provide empty-state handling
 * 
 * DATA SOURCES (in priority order):
 * 1. window.__RISKCAST_SUMMARY__ (server-injected)
 * 2. sessionStorage.getItem("riskcast_summary")
 * 3. fetch("/results/data") (primary API endpoint)
 * 
 * ENGINE-FIRST: This module only loads and normalizes data.
 * NO calculations, NO business logic, NO risk level derivation.
 */

/**
 * Normalize summary data to consistent schema
 * Handles different backend formats and key name variations
 * 
 * @param {Object} raw - Raw summary data from any source
 * @returns {Object} Normalized summary object
 */
export function normalizeSummary(raw) {
    if (!raw || typeof raw !== 'object') {
        return null;
    }
    
    // Extract shipment data
    const shipment = raw.shipment || {};
    const route = shipment.route || {};
    
    // Normalize route text
    let routeText = '';
    if (typeof route === 'string') {
        routeText = route;
    } else if (route.pol && route.pod) {
        routeText = `${route.pol} → ${route.pod}`;
    } else if (shipment.origin && shipment.destination) {
        routeText = `${shipment.origin} → ${shipment.destination}`;
    } else if (shipment.pol_code && shipment.pod_code) {
        routeText = `${shipment.pol_code} → ${shipment.pod_code}`;
    }
    
    // Extract risk data
    const risk = raw.risk || {};
    const overall = {
        riskScore: risk.finalScore != null ? risk.finalScore : 
                   raw.risk_score != null ? raw.risk_score :
                   raw.overall_risk != null ? raw.overall_risk :
                   raw.globalRisk != null ? raw.globalRisk : null,
        riskLevel: risk.level || raw.risk_level || raw.riskLevel || null,
        confidence: risk.confidence != null ? risk.confidence :
                    raw.confidence != null ? raw.confidence : null
    };
    
    // Normalize layers - remove duplicates and ensure proper structure
    const rawLayers = risk.layers || raw.layers || [];
    const layerMap = new Map();
    const normalizeLayerName = (name) => {
        if (!name) return '';
        return name.trim().toLowerCase().replace(/\s+/g, ' ');
    };
    
    rawLayers.forEach(layer => {
        if (!layer || !layer.name) return;
        const normalized = normalizeLayerName(layer.name);
        if (!layerMap.has(normalized)) {
            layerMap.set(normalized, {
                key: normalized,
                name: layer.name,
                icon: layer.icon || null,
                score: layer.score != null ? layer.score : null,
                contributionPct: layer.contribution != null ? 
                    (layer.contribution <= 1 ? layer.contribution * 100 : layer.contribution) : null,
                status: layer.status || null
            });
        }
    });
    
    const layers = Array.from(layerMap.values());
    
    // Extract financial data - check multiple sources
    const financialDist = raw.financial_distribution || {};
    const financial = raw.financial || {};
    const loss = raw.loss || {};
    const advancedMetrics = raw.advanced_metrics || {};
    
    const financialData = {
        meanLoss: financial.meanLoss != null ? financial.meanLoss :
                   loss.expectedLoss != null ? loss.expectedLoss :
                   financial.expectedLoss != null ? financial.expectedLoss :
                   financialDist.expected_loss_usd != null ? financialDist.expected_loss_usd : null,
        stdDev: financial.stdDev != null ? financial.stdDev :
                loss.stdDev != null ? loss.stdDev :
                financialDist.loss_std_usd != null ? financialDist.loss_std_usd : null,
        var95: financial.var95 != null ? financial.var95 :
               loss.p95 != null ? loss.p95 :
               financial.percentile95 != null ? financial.percentile95 :
               financialDist.var_95_usd != null ? financialDist.var_95_usd :
               advancedMetrics.var_95 != null ? advancedMetrics.var_95 : null,
        cvar: financial.cvar != null ? financial.cvar :
              loss.p99 != null ? loss.p99 :
              financial.maxLoss != null ? financial.maxLoss :
              financialDist.cvar_95_usd != null ? financialDist.cvar_95_usd :
              advancedMetrics.cvar_95 != null ? advancedMetrics.cvar_95 : null,
        expectedLoss: financial.expectedLoss != null ? financial.expectedLoss :
                      financial.meanLoss != null ? financial.meanLoss :
                      loss.expectedLoss != null ? loss.expectedLoss :
                      financialDist.expected_loss_usd != null ? financialDist.expected_loss_usd : null,
        maxLoss: financial.maxLoss != null ? financial.maxLoss :
                 financialDist.max_loss_usd != null ? financialDist.max_loss_usd : null,
        p95: financial.var95 != null ? financial.var95 :
             loss.p95 != null ? loss.p95 :
             financialDist.var_95_usd != null ? financialDist.var_95_usd : null,
        maxObserved: financial.maxLoss != null ? financial.maxLoss :
                     financialDist.max_loss_usd != null ? financialDist.max_loss_usd :
                     loss.p99 != null ? loss.p99 :
                     financial.cvar != null ? financial.cvar : null,
        cargoValue: financial.cargoValue != null ? financial.cargoValue :
                    shipment.value_usd != null ? shipment.value_usd :
                    shipment.cargo_value != null ? shipment.cargo_value :
                    shipment.value != null ? shipment.value :
                    raw.cargo_value != null ? raw.cargo_value :
                    raw.shipment_value != null ? raw.shipment_value :
                    raw.shipment?.cargo_value != null ? raw.shipment.cargo_value :
                    null
    };
    
    // Extract decision data
    const decision = raw.insuranceDecision || raw.decision || {};
    const shippingWindow = decision.shippingWindow || decision.timing || {};
    const decisionData = {
        insuranceRecommendation: decision.recommendation || null,
        safeWindow: {
            optimalStart: shippingWindow.optimalStart || null,
            optimalEnd: shippingWindow.optimalEnd || null,
            currentEtd: shippingWindow.currentETD || shipment.etd || null,
            riskReductionPts: shippingWindow.riskReduction != null ? shippingWindow.riskReduction : null
        },
        providers: (decision.providers || []).map((p, idx) => ({
            name: p.name || null,
            fitPct: p.fit != null ? (p.fit <= 1 ? p.fit * 100 : p.fit) : null,
            premium: p.premium != null ? p.premium : null,
            rank: idx + 1
        })),
        trace: (decision.trace || []).map(t => ({
            icon: t.icon || null,
            label: t.label || null,
            detail: t.detail || null
        }))
    };
    
    // Extract narrative data
    const narrative = raw.aiNarrative || raw.narrative || {};
    const narrativeData = {
        timestamp: narrative.generatedAt || raw.timestamp || null,
        summaryText: narrative.summary || narrative.summaryText || null,
        insights: (narrative.insights || []).map(i => ({
            type: i.type || null,
            title: i.title || null,
            text: i.text || null
        })),
        actions: narrative.actions || []
    };
    
    // Extract factors (for factor cards)
    const factors = (raw.factors || raw.risk_factors || []).map(f => ({
        name: f.name || f.factor || null,
        impactPct: f.impact != null ? (f.impact <= 1 ? f.impact * 100 : f.impact) : null,
        probabilityPct: f.probability != null ? (f.probability <= 1 ? f.probability * 100 : f.probability) : null,
        status: f.status || null
    }));
    
    return {
        shipment: {
            id: shipment.id || null,
            routeText: routeText,
            carrier: shipment.carrier || null,
            etd: shipment.etd || null
        },
        overall: overall,
        layers: layers,
        financial: financialData,
        decision: decisionData,
        narrative: narrativeData,
        factors: factors
    };
}

/**
 * Load summary data from multiple sources
 * Tries sources in priority order until data is found
 * 
 * CRITICAL: API is PRIORITY 1 to ensure fresh data from backend engine
 * 
 * @returns {Promise<Object|null>} Normalized summary or null if not found
 */
export async function loadSummaryData() {
    // ============================================================
    // PRIORITY 1: Backend API (ENGINE-FIRST - always fetch fresh data)
    // ============================================================
    // CRITICAL: API must be checked FIRST to ensure we get latest engine results
    // Add cache-busting to prevent browser from using stale cached responses
    const endpoints = [
        '/results/data',
        '/api/get_last_result'
    ];
    
    for (const endpoint of endpoints) {
        try {
            // Add cache-busting timestamp to ensure fresh data
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
            
            if (response.ok) {
                const data = await response.json();
                // Check for valid data (not empty object, not error response)
                if (data && typeof data === 'object' && !data.error && Object.keys(data).length > 0) {
                    const riskScore = data.risk?.finalScore || data.risk_score || data.overall_risk;
                    const layers = data.risk?.layers || data.layers || [];
                    const cargoValue = data.shipment?.value_usd || data.cargo_value || data.shipment?.cargo_value;
                    
                    console.log(`[ResultsOS] ✓ Data source: ${endpoint}`, {
                        timestamp: new Date().toISOString(),
                        riskScore: riskScore,
                        riskLevel: data.risk?.level || data.risk_level,
                        layersCount: layers.length,
                        layerNames: layers.slice(0, 5).map(l => l.name || l).join(', '),
                        hasFinancial: !!(data.financial || data.financial_distribution),
                        cargoValue: cargoValue,
                        expectedLoss: data.financial?.expectedLoss || data.financial_distribution?.expected_loss_usd,
                        var95: data.financial?.var95 || data.financial_distribution?.var_95_usd
                    });
                    return normalizeSummary(data);
                } else {
                    console.warn(`[ResultsOS] ✗ ${endpoint} returned invalid/empty data:`, data);
                }
            } else {
                console.warn(`[ResultsOS] ✗ ${endpoint} returned status ${response.status}`);
            }
        } catch (e) {
            // Log error but continue to next endpoint
            console.warn(`[ResultsOS] ✗ Failed to fetch from ${endpoint}:`, e.message);
            continue;
        }
    }
    
    // ============================================================
    // PRIORITY 2: window.__RISKCAST_SUMMARY__ (server-injected, may be stale)
    // ============================================================
    // WARNING: This may contain old data if server cached the template
    // Only use as fallback if API fails
    if (typeof window !== 'undefined' && window.__RISKCAST_SUMMARY__) {
        console.warn('[ResultsOS] ⚠ Using window.__RISKCAST_SUMMARY__ (may be stale - API failed)');
        return normalizeSummary(window.__RISKCAST_SUMMARY__);
    }
    
    // ============================================================
    // PRIORITY 3: sessionStorage (legacy fallback)
    // ============================================================
    try {
        const sessionData = sessionStorage.getItem('riskcast_summary');
        if (sessionData) {
            const parsed = JSON.parse(sessionData);
            console.warn('[ResultsOS] ⚠ Using sessionStorage (legacy fallback - API failed)');
            return normalizeSummary(parsed);
        }
    } catch (e) {
        console.warn('[ResultsOS] Failed to parse sessionStorage data:', e);
    }
    
    // No data found from any source
    console.error('[ResultsOS] ✗ No summary data found from any source (API, window, or storage)');
    return null;
}

/**
 * Show empty state banner when no data is available
 */
export function showEmptyState() {
    const resultsPage = document.querySelector('.results-page');
    if (!resultsPage) return;
    
    const banner = document.createElement('div');
    banner.className = 'empty-state-banner';
    banner.innerHTML = `
        <div class="empty-state-content">
            <h2>No Summary Data Available</h2>
            <p>Please run a risk analysis first to view results.</p>
            <a href="/summary" class="empty-state-link">Go to Analysis →</a>
        </div>
    `;
    
    resultsPage.insertBefore(banner, resultsPage.firstChild);
}


