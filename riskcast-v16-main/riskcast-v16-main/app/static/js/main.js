/**
 * ResultsOS Main Orchestration
 * 
 * Mounts all ResultsOS components using data from state.js.
 * This file is orchestration ONLY - no business logic, no data transformation.
 * 
 * ARCHITECTURAL PRINCIPLES:
 * - Separation of Concerns: All business logic resides in state.js (pure functions)
 * - Immutability: State is frozen after computation to ensure academic/enterprise auditability
 * - Presentation Layer: Components receive pre-computed data, no decision logic in UI
 * - Traceability: All recommendations include decision trace explaining triggers and thresholds
 * 
 * DECISION SUPPORT DISCLAIMER:
 * This system provides decision support recommendations based on risk assessment models.
 * All outputs are deterministic calculations from provided inputs, not predictive guarantees.
 * Insurance recommendations, shipping windows, and provider rankings are advisory only.
 * Final decisions remain the responsibility of the user and should be validated with
 * qualified professionals (insurance brokers, logistics experts, legal counsel).
 * 
 * @file main.js
 */

import { resultsState, loadSummaryState, loadSummaryStateWithAPI, transformSummaryToResults, transformBackendAPIToResults } from './state.js';
import { renderResults, renderFinancialImpact } from './resultsRenderer.js';
import { loadSummaryData, normalizeSummary, showEmptyState } from './results.js';

/**
 * Debug flag: Controls verbose console logging for development and competition demo
 * Set to false in production to reduce console noise
 * @type {boolean}
 */
const DEBUG = false; // Set to false for production

/**
 * Freeze default state to prevent accidental mutation
 * Immutable snapshot ensures academic/enterprise review integrity
 */
Object.freeze(resultsState);

/**
 * NEW ARCHITECTURE: Static HTML + Renderer
 * Component imports removed - using static HTML with resultsRenderer.js
 * All rendering is handled by renderer, no component mounting needed
 */

/**
 * Normalize risk level string format for UI components
 * ARCHITECTURE: ENGINE-FIRST
 * Backend MUST provide risk level already computed
 * This function only normalizes string format (display formatting, NOT computation)
 * 
 * @param {string} riskLevel - Risk level from backend (e.g., 'Low', 'MEDIUM', 'high', 'Critical')
 * @returns {string} Normalized risk level: 'low', 'medium', or 'high'
 */
function normalizeRiskLevelForUI(riskLevel) {
  if (!riskLevel) return 'low';
  
  const levelLower = String(riskLevel).toLowerCase();
  
  // Map backend format to normalized format (UI formatting only)
  if (levelLower.includes('high') || levelLower.includes('critical')) return 'high';
  if (levelLower.includes('medium') || levelLower.includes('moderate')) return 'medium';
  return 'low';
}

/**
 * NEW ARCHITECTURE: Component mounting removed
 * Using static HTML + renderer approach instead
 * All rendering handled by resultsRenderer.js
 */

/**
 * Render traceability block as read-only HTML
 * @param {string} slotId - DOM element ID
 * @param {Object} state - Active state object
 */
function renderTraceability(slotId, state = resultsState) {
  const element = document.getElementById(slotId);
  if (!element) {
    console.warn(`ResultsOS: Slot #${slotId} not found, skipping traceability render`);
    return;
  }

  const traceability = state.traceability || resultsState.traceability;
  if (!traceability) {
    console.warn('ResultsOS: Traceability data not found in state');
    return;
  }

  const decisionBasis = traceability.decisionBasis || [];
  const references = traceability.references || [];
  
  // Add decision engine trace if available
  const recommendations = state.recommendations;
  const decisionTrace = recommendations?.trace;

  // Create collapsible structure (collapsed by default)
  const uniqueId = `traceability-${Date.now()}`;
  element.innerHTML = `
    <details class="traceability-details" id="${uniqueId}">
      <summary class="traceability-summary">
        <span class="traceability-summary-text">Truy Vết Phương Pháp & Kiểm Toán (Đánh Giá Học Thuật)</span>
        <span class="traceability-summary-icon">▼</span>
      </summary>
      <div class="traceability-wrapper">
        <div class="traceability-basis">
          <h3 class="traceability-subtitle">Cơ Sở Quyết Định</h3>
          <ul class="traceability-list">
            ${decisionBasis.map(basis => `<li class="traceability-item">${escapeHtml(basis)}</li>`).join('')}
          </ul>
        </div>

        ${references.length > 0 ? `
        <div class="traceability-references">
          <h3 class="traceability-subtitle">Tài Liệu Tham Khảo</h3>
          <ul class="traceability-list">
            ${references.map(ref => `<li class="traceability-item">${escapeHtml(ref)}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        ${decisionTrace ? `
        <div class="traceability-decision-engine">
          <h3 class="traceability-subtitle">Truy Vết Động Cơ Quyết Định</h3>
          <div class="traceability-decision-engine-meta">
            <span class="traceability-decision-engine-version">Phiên bản: ${escapeHtml(decisionTrace.version || 'unknown')}</span>
          </div>
          ${decisionTrace.dominantSignals && decisionTrace.dominantSignals.length > 0 ? `
          <div class="traceability-decision-engine-signals">
            <h4 class="traceability-decision-engine-signals-title">Tín Hiệu Chủ Đạo</h4>
            <div class="traceability-decision-engine-signals-list">
              ${decisionTrace.dominantSignals.map(signal => `<span class="traceability-decision-engine-signal-tag">${escapeHtml(signal)}</span>`).join('')}
            </div>
          </div>
          ` : ''}
          ${decisionTrace.triggers && decisionTrace.triggers.length > 0 ? `
          <div class="traceability-decision-engine-triggers">
            <h4 class="traceability-decision-engine-triggers-title">Các Kích Hoạt</h4>
            <ul class="traceability-list">
              ${decisionTrace.triggers.map(trigger => `
                <li class="traceability-item">
                  <strong>${escapeHtml(trigger.signal || 'Unknown')}</strong> 
                  (Giá trị: ${escapeHtml(trigger.value || 'N/A')}, Ngưỡng: ${escapeHtml(trigger.threshold || 'N/A')}, 
                  Tác động: ${escapeHtml(trigger.impact || 'LOW')}) - 
                  ${escapeHtml(trigger.note || '')}
                </li>
              `).join('')}
            </ul>
          </div>
          ` : ''}
        </div>
        ` : ''}
      </div>
    </details>
  `;

  // Add toggle icon animation
  const detailsEl = element.querySelector(`#${uniqueId}`);
  if (detailsEl) {
    detailsEl.addEventListener('toggle', function() {
      const icon = this.querySelector('.traceability-summary-icon');
      if (icon) {
        icon.textContent = this.open ? '▲' : '▼';
      }
    });
  }

  // Inject styles if not already present
  if (!document.getElementById('traceability-styles')) {
    const style = document.createElement('style');
    style.id = 'traceability-styles';
    style.textContent = `
      .traceability-details {
        background: rgba(15, 15, 20, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, system-ui, sans-serif;
      }

      .traceability-summary {
        padding: 20px 32px;
        cursor: pointer;
        list-style: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
        user-select: none;
        transition: background-color 0.2s ease;
      }

      .traceability-summary::-webkit-details-marker {
        display: none;
      }

      .traceability-summary:hover {
        background-color: rgba(255, 255, 255, 0.03);
      }

      .traceability-summary-text {
        font-size: 16px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.85);
        letter-spacing: -0.2px;
      }

      .traceability-summary-icon {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
        transition: transform 0.2s ease;
      }

      .traceability-wrapper {
        padding: 0 32px 32px 32px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        margin-top: 0;
      }

      .traceability-title {
        font-size: 20px;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin: 0 0 24px 0;
        letter-spacing: -0.3px;
      }

      .traceability-subtitle {
        font-size: 16px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.85);
        margin: 0 0 16px 0;
      }

      .traceability-basis {
        margin-bottom: 32px;
      }

      .traceability-references {
        padding-top: 24px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
      }

      .traceability-list {
        list-style: none;
        padding: 0;
        margin: 0;
      }

      .traceability-item {
        font-size: 14px;
        line-height: 1.7;
        color: rgba(255, 255, 255, 0.75);
        margin-bottom: 12px;
        padding-left: 24px;
        position: relative;
      }

      .traceability-item::before {
        content: '•';
        position: absolute;
        left: 0;
        color: rgba(255, 255, 255, 0.4);
        font-size: 18px;
        line-height: 1.5;
      }

      .traceability-item:last-child {
        margin-bottom: 0;
      }

      @media (max-width: 768px) {
        .traceability-wrapper {
          padding: 24px 20px;
        }

        .traceability-title {
          font-size: 18px;
        }

        .traceability-subtitle {
          font-size: 15px;
        }

        .traceability-item {
          font-size: 13px;
        }
      }
    `;
    document.head.appendChild(style);
  }
}

/**
 * Escape HTML to prevent XSS
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
  if (str == null) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

/**
 * Verify ResultsOS DOM structure exists
 * New static HTML structure - verify .results-page exists
 * @private
 */
function createResultsOSStructure() {
  const resultsPage = document.querySelector('.results-page');
  if (!resultsPage) {
    console.error('ResultsOS: .results-page container not found');
    return false;
  }
  
  return true;
}

/**
 * Initialize all ResultsOS components
 * NEW ARCHITECTURE: Static HTML + Renderer (no component mounting)
 */
async function initResultsOS() {
  // Verify DOM structure exists (static HTML provides structure)
  if (!createResultsOSStructure()) {
    console.error('ResultsOS: DOM structure verification failed');
    return;
  }

  // ============================================================
  // ARCHITECTURE: ENGINE-FIRST - Data Loading
  // ============================================================
  // CRITICAL: Results page NEVER triggers engine execution
  // - This function ONLY reads data (GET /results/data)
  // - Engine is executed ONLY in Summary page (POST /api/v1/risk/v2/analyze)
  // - No duplicate execution, no UI-side computation
  // ============================================================
  // Load summary state: Priority 1 = Backend API (direct from calculation algorithm), Priority 2 = Storage
  // loadSummaryStateWithAPI() already transforms the data to ResultsOS format
  const transformedState = await loadSummaryStateWithAPI();
  let activeState = resultsState;
  
  // ============================================================
  // STATE TRANSFORMATION (Orchestration: delegates to state.js)
  // ============================================================
  
  // Use transformed state if available (already in ResultsOS format from loadSummaryStateWithAPI)
  if (transformedState) {
    try {
      activeState = transformedState;
      // Merge with static metadata (methodology, traceability from default state)
      activeState.meta = activeState.meta || resultsState.meta;
      activeState.methodology = activeState.methodology || resultsState.methodology;
      activeState.traceability = activeState.traceability || resultsState.traceability;
      
      if (DEBUG) {
        console.log('ResultsOS: Using data from backend API (calculation algorithm)', {
          globalRisk: activeState.globalRisk,
          layersCount: activeState.layers?.length || 0,
          source: activeState.meta?.source || 'unknown'
        });
      }
    } catch (error) {
      console.error('ResultsOS: Failed to use transformed state', error);
      // Fall back to default state - graceful degradation
      activeState = resultsState;
    }
  } else {
    // No data available - use default state (demo/fallback mode)
    if (DEBUG) {
      console.log('ResultsOS: No data found (backend API or storage), using default state', {
        globalRisk: resultsState.globalRisk,
        layersCount: resultsState.layers?.length || 0
      });
    }
    activeState = resultsState;
  }
  
  // ============================================================
  // RENDER RESULTS PAGE (ENGINE-FIRST: Map summary to DOM)
  // ============================================================
  // Try new data loader first, then fallback to old system
  let normalizedSummary = null;
  try {
    console.log('[ResultsOS] 🔄 Fetching fresh data from backend API...');
    normalizedSummary = await loadSummaryData();
    
    if (normalizedSummary) {
      const layers = normalizedSummary.layers || [];
      console.log('[ResultsOS] ✓ Data loaded successfully', {
        source: 'loadSummaryData()',
        riskScore: normalizedSummary.overall?.riskScore,
        riskLevel: normalizedSummary.overall?.riskLevel,
        confidence: normalizedSummary.overall?.confidence,
        layersCount: layers.length,
        layerNames: layers.slice(0, 5).map(l => l.name).join(', '),
        hasFinancial: !!normalizedSummary.financial,
        cargoValue: normalizedSummary.financial?.cargoValue,
        expectedLoss: normalizedSummary.financial?.expectedLoss,
        var95: normalizedSummary.financial?.var95,
        timestamp: new Date().toISOString()
      });
    } else {
      console.warn('[ResultsOS] ⚠ No data from loadSummaryData(), will try legacy system');
    }
  } catch (e) {
    console.error('[ResultsOS] ✗ New data loader failed:', e);
    console.warn('[ResultsOS] Falling back to legacy system...');
  }
  
  // If new loader found data, use it; otherwise use legacy activeState
  let summaryForRenderer;
  if (normalizedSummary) {
    // Use normalized summary from results.js
    summaryForRenderer = normalizedSummary;
    if (DEBUG) {
      console.log('[ResultsOS] Using normalized summary from results.js', summaryForRenderer);
    }
  } else {
    // Fallback to legacy activeState transformation
    // Convert activeState to summary format for renderer
    // CRITICAL: Extract pol/pod from various route formats
    const shipment = activeState.shipment || {};
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
    
    summaryForRenderer = {
      shipment: {
        id: shipment.id,
        routeText: pol && pod ? `${pol} → ${pod}` : shipment.route || '',
        carrier: shipment.carrier,
        etd: shipment.eta || shipment.etd
      },
      overall: {
        riskScore: activeState.globalRisk || null,
        riskLevel: activeState.decision?.riskLevel || activeState.profile?.level || null,
        confidence: activeState.decision?.confidence || activeState.profile?.confidence || null
      },
      layers: (() => {
        // Map and filter layers
        const mappedLayers = activeState.layers?.map(l => ({
          name: l.name || null,
          score: l.score != null ? l.score : null,
          contributionPct: l.contribution != null ? 
            (l.contribution <= 1 ? l.contribution * 100 : l.contribution) : null,
          status: l.status || null
        })).filter(l => l.name && l.score != null) || [];
        
        // Remove duplicates by layer name (case-insensitive)
        const normalizeName = (name) => name.trim().toLowerCase().replace(/\s+/g, ' ');
        const seen = new Map();
        const unique = [];
        
        mappedLayers.forEach(layer => {
          const normalized = normalizeName(layer.name);
          if (!seen.has(normalized)) {
            seen.set(normalized, true);
            unique.push(layer);
          } else {
            // Only log in debug mode to reduce console noise
            if (DEBUG) {
              console.debug(`[ResultsOS] Duplicate layer filtered: "${layer.name}"`);
            }
          }
        });
        
        return unique;
      })(),
      financial: (() => {
        // Try financial object first (from state.js mapping), then fallback to loss
        const financial = activeState.financial || {};
        const loss = activeState.loss || {};
        
        // DEBUG: Log financial data extraction
        if (DEBUG) {
          console.log('[Main] Extracting financial data:', {
            activeStateFinancial: financial,
            activeStateLoss: loss,
            shipmentValue: activeState.shipment?.value_usd || activeState.shipment?.cargo_value
          });
        }
        
        const financialData = {
          expectedLoss: financial.expectedLoss || loss.expectedLoss || null,
          meanLoss: financial.meanLoss || financial.expectedLoss || loss.expectedLoss || null,
          var95: financial.var95 || financial.percentile95 || loss.p95 || null,
          percentile95: financial.percentile95 || financial.var95 || loss.p95 || null,
          cvar: financial.cvar || loss.p99 || loss.cvar || null,
          maxLoss: financial.maxLoss || loss.maxLoss || null,
          maxObserved: financial.maxLoss || financial.maxObserved || loss.p99 || loss.cvar || null,
          stdDev: financial.stdDev || loss.stdDev || null,
          cargoValue: financial.cargoValue || activeState.shipment?.value_usd || activeState.shipment?.cargo_value || null
        };
        
        if (DEBUG) {
          console.log('[Main] Final financial data for renderer:', financialData);
        }
        
        return financialData;
      })(),
      decision: activeState.recommendations?.insurance ? {
        insuranceRecommendation: activeState.recommendations.insurance.required ? 'BUY' : 'OPTIONAL',
        safeWindow: {
          optimalStart: activeState.recommendations.timing?.optimalStart || null,
          optimalEnd: activeState.recommendations.timing?.optimalEnd || null,
          currentEtd: activeState.recommendations.timing?.currentETD || shipment.etd || null,
          riskReductionPts: activeState.recommendations.timing?.riskReduction || null
        },
        providers: (activeState.recommendations.providers || []).map((p, idx) => ({
          name: p.name || null,
          fitPct: p.fit != null ? (p.fit <= 1 ? p.fit * 100 : p.fit) : null,
          premium: p.premium != null ? p.premium : null,
          rank: idx + 1
        })),
        trace: (activeState.recommendations.trace?.triggers || []).map(t => ({
          icon: null,
          label: t.signal || 'Signal',
          detail: `${t.note || ''} (Value: ${t.value}, Threshold: ${t.threshold})`
        }))
      } : null,
      narrative: {
        timestamp: activeState.meta?.timestamp || null,
        summaryText: activeState.decision?.decisionRationale?.[0] || activeState.decision?.explanation || null,
        insights: (activeState.factors?.slice(0, 3) || []).map(f => ({
          type: f.type || null,
          title: f.factor || f.name || null,
          text: f.text || f.description || null
        })).filter(i => i.title && i.text),
        actions: activeState.recommendations?.actions || []
      },
      factors: (activeState.factors || []).map(f => ({
        name: f.factor || f.name || null,
        impactPct: f.impact != null ? (f.impact <= 1 ? f.impact * 100 : f.impact) : null,
        probabilityPct: f.probability != null ? (f.probability <= 1 ? f.probability * 100 : f.probability) : null,
        status: f.status || null
      }))
    };
  }
  
  // Render static HTML with data
  if (summaryForRenderer && (
    summaryForRenderer.overall?.riskScore != null ||
    summaryForRenderer.risk?.finalScore != null ||
    (summaryForRenderer.layers && summaryForRenderer.layers.length > 0)
  )) {
    // Log summary before rendering (always log for debugging)
    const layers = summaryForRenderer.layers || [];
    console.log('[ResultsOS] 🎨 Rendering results page with data:', {
      riskScore: summaryForRenderer.overall?.riskScore || summaryForRenderer.risk?.finalScore,
      riskLevel: summaryForRenderer.overall?.riskLevel,
      confidence: summaryForRenderer.overall?.confidence,
      layersCount: layers.length,
      layerNames: layers.slice(0, 5).map(l => l.name).join(', '),
      hasFinancial: !!summaryForRenderer.financial,
      financialKeys: summaryForRenderer.financial ? Object.keys(summaryForRenderer.financial) : [],
      cargoValue: summaryForRenderer.financial?.cargoValue,
      expectedLoss: summaryForRenderer.financial?.expectedLoss,
      var95: summaryForRenderer.financial?.var95,
      timestamp: new Date().toISOString()
    });
    
    renderResults(summaryForRenderer);
    
    // Force re-render financial impact after a short delay to ensure DOM is ready
    // IMPORTANT: Pass scenario from summary to prevent re-classification and ensure empty states persist
    setTimeout(() => {
      if (summaryForRenderer.financial) {
        // Use scenario that was already computed and attached to summary by renderResults
        const scenarioForRerender = summaryForRenderer.scenario;
        renderFinancialImpact(summaryForRenderer, scenarioForRerender);
      }
    }, 500);
  } else {
    // No data available - show empty state
    showEmptyState();
    console.warn('[ResultsOS] No valid summary data available - showing empty state');
  }
  
  // ============================================================
  // DECISION INTELLIGENCE: Recommendations
  // ============================================================
  // ARCHITECTURE: ENGINE-FIRST
  // Recommendations MUST come from backend (Python Engine v2)
  // Backend provides complete recommendations object in activeState.recommendations
  // Frontend does NOT compute recommendations - only consumes them
  
  // Freeze recommendations from backend (if present)
  if (activeState.recommendations) {
    Object.freeze(activeState.recommendations);
    if (activeState.recommendations.insurance) Object.freeze(activeState.recommendations.insurance);
    if (activeState.recommendations.timing) Object.freeze(activeState.recommendations.timing);
    if (activeState.recommendations.providers) {
      Object.freeze(activeState.recommendations.providers);
      activeState.recommendations.providers.forEach(p => Object.freeze(p));
    }
    if (activeState.recommendations.trace) Object.freeze(activeState.recommendations.trace);
    
    if (DEBUG) {
      console.log('ResultsOS: Using recommendations from backend', {
        insuranceRequired: activeState.recommendations.insurance?.required,
        insuranceLevel: activeState.recommendations.insurance?.level,
        providersCount: activeState.recommendations.providers?.length || 0
      });
    }
  } else {
    if (DEBUG) {
      console.warn('ResultsOS: No recommendations provided by backend - component will show empty state UI');
    }
  }
  
  // ============================================================
  // STATE IMMUTABILITY: Freeze all computed state
  // ============================================================
  // CRITICAL for academic/enterprise review: frozen state ensures
  // no accidental mutation and provides audit trail integrity
  Object.freeze(activeState);
  if (activeState.layers) Object.freeze(activeState.layers);
  if (activeState.factors) Object.freeze(activeState.factors);
  if (activeState.decision) Object.freeze(activeState.decision);
  if (activeState.shipment) Object.freeze(activeState.shipment);
  if (activeState.charts) Object.freeze(activeState.charts);
  
  if (DEBUG) {
    console.log('ResultsOS: Active state structure', {
      globalRisk: activeState.globalRisk,
      layers: activeState.layers?.length || 0,
      hasDecision: !!activeState.decision,
      hasCharts: !!activeState.charts,
      hasRecommendations: !!activeState.recommendations
    });
  }
  
  // Enterprise initialization log with metadata (always logged for audit trail)
  if (activeState.meta && activeState.meta.version) {
    const metadata = {
      version: activeState.meta.version,
      timestamp: activeState.meta?.timestamp || new Date().toISOString(),
      dataSource: activeState.meta?.source || 'default_state',
      modelVersion: activeState.methodology?.riskAggregation?.model || 'FAHP',
      stateFrozen: true,
      recommendationsFrozen: !!activeState.recommendations
    };
    console.info(`ResultsOS ${activeState.meta.version} initialized`, metadata);
  }

  // ============================================================
  // NEW ARCHITECTURE: Static HTML + Renderer
  // ============================================================
  // All rendering is handled by resultsRenderer.js
  // No component mounting needed - HTML is static, renderer populates data

  // ============================================================
  // DEBUG EXPOSURE: Expose state for development/debugging
  // ============================================================
  // Exposes frozen state to window for debugging
  // All exposed data is frozen (immutable) to maintain audit trail integrity
  if (typeof window !== 'undefined') {
    window.__RESULTSOS__ = {
      state: activeState, // Frozen state object (from backend API or storage)
      summary: summaryForRenderer, // Summary format used by renderer
      recommendations: activeState.recommendations || null // Frozen recommendations
    };
    
    if (DEBUG) {
      console.log('ResultsOS: State exposed to window.__RESULTSOS__ for debugging');
    }
  }
}

/**
 * Initialize collapsible section toggle icons
 * NEW ARCHITECTURE: Static HTML - no dynamic collapsibles needed
 * All HTML is static, renderer populates data only
 */
function initCollapsibleSections() {
  // Static HTML approach - no initialization needed
  // All collapsible sections are handled by native HTML <details> elements
}

// Initialize on DOM content loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initResultsOS);
} else {
  // DOM already loaded
  initResultsOS();
}
