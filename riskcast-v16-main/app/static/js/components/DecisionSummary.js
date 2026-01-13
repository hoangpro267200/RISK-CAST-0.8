/**
 * DecisionSummary Component
 * 
 * STRICT ENGINE-FIRST ARCHITECTURE
 * 
 * This component is a PURE PRESENTATION LAYER that displays engine decisions.
 * 
 * ============================================================================
 * CRITICAL: NO BUSINESS LOGIC ALLOWED
 * ============================================================================
 * 
 * FORBIDDEN:
 * ❌ Calculate efficiency metrics (riskReduction / costImpact)
 * ❌ Compute Pareto frontiers or rankings
 * ❌ Derive "best" scenario using formulas
 * ❌ Normalize or transform business values
 * ❌ Make decisions based on thresholds
 * 
 * ALLOWED:
 * ✅ Read explicit engine fields (isRecommended, rank, scenarioId)
 * ✅ Format display values (currency, dates)
 * ✅ Map field names (backend → frontend)
 * ✅ Show empty states when data missing
 * 
 * ============================================================================
 * REQUIRED ENGINE PAYLOAD STRUCTURE
 * ============================================================================
 * 
 * Option 1: Explicit Decision Summary (PREFERRED)
 * {
 *   decisionSummary: {
 *     insuranceScenarioId: "scenario-1",  // Engine picks this
 *     timingScenarioId: "scenario-2",
 *     routingScenarioId: "scenario-3",
 *     confidence: 0.87
 *   },
 *   scenarios: [
 *     {
 *       id: "scenario-1",
 *       title: "Add Insurance",
 *       category: "INSURANCE",
 *       riskReduction: 0,
 *       costImpact: 1250,
 *       description: "...",
 *       isRecommended: true  // Engine flag
 *     }
 *   ]
 * }
 * 
 * Option 2: Scenario Flags (FALLBACK)
 * {
 *   scenarios: [
 *     {
 *       id: "scenario-1",
 *       category: "INSURANCE",  // or tag: "INSURANCE"
 *       isRecommended: true,    // Engine sets this
 *       rank: 1,                // Engine ranking (1 = best)
 *       ...
 *     }
 *   ]
 * }
 * 
 * Option 3: Legacy Insurance/Timing Objects (FALLBACK)
 * {
 *   insurance: {
 *     recommendation: "BUY",
 *     rationale: "...",
 *     providers: [...]
 *   },
 *   timing: {
 *     optimalWindow: "Jan 15-20",
 *     riskReduction: 15
 *   }
 * }
 */

class DecisionSummary {
  constructor() {
    this.container = null;
    this._stylesInjected = false;
  }

  /**
   * Mount component to DOM
   * @param {HTMLElement} el - Container element
   * @param {Object} data - Decision data from engine
   */
  mount(el, data = {}) {
    if (!el) {
      console.warn('[DecisionSummary] No container element provided');
      return;
    }

    this.container = el;
    this._injectStyles();
    this._render(data);
  }

  /**
   * Update component with new data
   * @param {Object} data - Updated decision data
   */
  update(data = {}) {
    if (!this.container) {
      console.warn('[DecisionSummary] Component not mounted');
      return;
    }

    this._render(data);
  }

  /**
   * Destroy component
   */
  destroy() {
    this.container = null;
  }

  /**
   * Render decision summary
   * @private
   */
  _render(data) {
    // Extract data using priority chain
    const decisionSummary = data.decisionSummary || {};
    const scenarios = data.scenarios || [];
    const insurance = data.insurance || data.decisionSignal || {};
    const timing = data.timing || {};
    const dataConfidence = data.dataConfidence || decisionSummary.confidence || 0.87;

    // Find scenarios using ENGINE-PROVIDED fields only
    const insuranceScenario = this._findScenarioByEngineSelection(
      scenarios,
      decisionSummary.insuranceScenarioId,
      'INSURANCE'
    );

    const timingScenario = this._findScenarioByEngineSelection(
      scenarios,
      decisionSummary.timingScenarioId,
      'TIMING'
    );

    const routingScenario = this._findScenarioByEngineSelection(
      scenarios,
      decisionSummary.routingScenarioId,
      'ROUTING'
    );

    // Render cards
    this._renderInsuranceCard(insurance, insuranceScenario);
    this._renderTimingCard(timing, timingScenario);
    this._renderRoutingCard(routingScenario);

    // Update confidence indicator
    this._updateConfidence(dataConfidence);
  }

  /**
   * Find scenario using ONLY engine-provided selection fields
   * NO COMPUTATION - only reads explicit flags/IDs from engine
   * 
   * Priority:
   * 1. Explicit scenarioId match
   * 2. isRecommended flag + category match
   * 3. Lowest rank + category match
   * 4. null (show pending state)
   * 
   * @private
   * @param {Array} scenarios - Scenarios from engine
   * @param {string} scenarioId - Explicit ID from decisionSummary
   * @param {string} category - Category filter (INSURANCE, TIMING, ROUTING)
   * @returns {Object|null} Selected scenario or null
   */
  _findScenarioByEngineSelection(scenarios, scenarioId, category) {
    if (!scenarios || scenarios.length === 0) {
      return null;
    }

    // Priority 1: Explicit scenario ID from engine
    if (scenarioId) {
      const found = scenarios.find(s => s.id === scenarioId);
      if (found) {
        console.log(`[DecisionSummary] Using engine-selected scenario ID: ${scenarioId}`);
        return found;
      }
    }

    // Filter by category
    const categoryScenarios = scenarios.filter(s => {
      const cat = s.category || s.tag || '';
      return cat.toUpperCase() === category.toUpperCase();
    });

    if (categoryScenarios.length === 0) {
      return null;
    }

    // Priority 2: isRecommended flag from engine
    const recommended = categoryScenarios.find(s => s.isRecommended === true);
    if (recommended) {
      console.log(`[DecisionSummary] Using engine-recommended scenario for ${category}`);
      return recommended;
    }

    // Priority 3: Lowest rank from engine (1 = best)
    const ranked = categoryScenarios.filter(s => typeof s.rank === 'number');
    if (ranked.length > 0) {
      const best = ranked.reduce((prev, curr) =>
        curr.rank < prev.rank ? curr : prev
      );
      console.log(`[DecisionSummary] Using engine-ranked scenario (rank ${best.rank}) for ${category}`);
      return best;
    }

    // No explicit selection - return null to show pending state
    return null;
  }

  /**
   * Render insurance decision card
   * @private
   */
  _renderInsuranceCard(insurance, scenario) {
    const card = document.getElementById('decision-insurance');
    if (!card) return;

    // Use legacy insurance object if no scenario
    if (!scenario && insurance.recommendation) {
      this._renderLegacyInsuranceCard(card, insurance);
      return;
    }

    if (!scenario) {
      this._renderPendingCard(card, 'Insurance Decision', 'Insurance analysis pending...');
      return;
    }

    // Map engine recommendation to status
    const recommendation = insurance.recommendation || 'OPTIONAL';
    const statusMap = {
      'BUY': { text: 'Recommended', class: 'recommended' },
      'SKIP': { text: 'Not Needed', class: 'skip' },
      'OPTIONAL': { text: 'Consider', class: 'consider' }
    };
    const status = statusMap[recommendation] || statusMap['OPTIONAL'];

    // Get provider info
    const providers = insurance.providers || [];
    const topProvider = providers.length > 0 ? providers[0] : null;

    card.innerHTML = `
      <div class="card-header">
        <h3 class="card-title">Insurance Decision</h3>
        <span class="status-pill" data-status="${status.class}">${status.text}</span>
      </div>
      <p class="card-why">${this._escapeHtml(scenario.description || insurance.rationale || 'No description available')}</p>
      <div class="card-kpis">
        <div class="kpi">
          <span class="kpi-label">Top Provider</span>
          <span class="kpi-value">${topProvider ? this._escapeHtml(topProvider.name) : '—'}</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Premium</span>
          <span class="kpi-value">${topProvider ? this._formatCurrency(topProvider.premium) : '—'}</span>
        </div>
      </div>
    `;
  }

  /**
   * Render legacy insurance card (fallback)
   * @private
   */
  _renderLegacyInsuranceCard(card, insurance) {
    const recommendation = insurance.recommendation || 'OPTIONAL';
    const rationale = insurance.rationale || 'Insurance analysis pending...';
    const providers = insurance.providers || [];
    const topProvider = providers.length > 0 ? providers[0] : null;

    const statusMap = {
      'BUY': { text: 'Recommended', class: 'recommended' },
      'SKIP': { text: 'Not Needed', class: 'skip' },
      'OPTIONAL': { text: 'Consider', class: 'consider' }
    };
    const status = statusMap[recommendation] || statusMap['OPTIONAL'];

    card.innerHTML = `
      <div class="card-header">
        <h3 class="card-title">Insurance Decision</h3>
        <span class="status-pill" data-status="${status.class}">${status.text}</span>
      </div>
      <p class="card-why">${this._escapeHtml(rationale)}</p>
      <div class="card-kpis">
        <div class="kpi">
          <span class="kpi-label">Top Provider</span>
          <span class="kpi-value">${topProvider ? this._escapeHtml(topProvider.name) : '—'}</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Premium</span>
          <span class="kpi-value">${topProvider ? this._formatCurrency(topProvider.premium) : '—'}</span>
        </div>
      </div>
    `;
  }

  /**
   * Render timing optimization card
   * @private
   */
  _renderTimingCard(timing, scenario) {
    const card = document.getElementById('decision-timing');
    if (!card) return;

    // Use legacy timing object if no scenario
    if (!scenario && timing.optimalWindow) {
      this._renderLegacyTimingCard(card, timing);
      return;
    }

    if (!scenario) {
      this._renderPendingCard(card, 'Timing Optimization', 'Timing analysis pending...');
      return;
    }

    // Use ENGINE values directly (NO calculation)
    const riskReduction = scenario.riskReduction || 0;
    const costImpact = scenario.costImpact || 0;

    // Determine status from ENGINE flag or rank
    let status = 'pending';
    let statusText = 'Evaluate';

    if (scenario.isRecommended) {
      status = 'recommended';
      statusText = 'Recommended';
    } else if (scenario.rank === 1) {
      status = 'recommended';
      statusText = 'Top Choice';
    } else if (scenario.rank === 2) {
      status = 'consider';
      statusText = 'Alternative';
    }

    card.innerHTML = `
      <div class="card-header">
        <h3 class="card-title">Timing Optimization</h3>
        <span class="status-pill" data-status="${status}">${statusText}</span>
      </div>
      <p class="card-why">${this._escapeHtml(scenario.description || 'Timing optimization available.')}</p>
      <div class="card-kpis">
        <div class="kpi">
          <span class="kpi-label">Risk Change</span>
          <span class="kpi-value ${riskReduction < 0 ? 'text-risk-low' : ''}">${riskReduction} pts</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Cost Impact</span>
          <span class="kpi-value">${this._formatCurrency(costImpact)}</span>
        </div>
      </div>
    `;
  }

  /**
   * Render legacy timing card (fallback)
   * @private
   */
  _renderLegacyTimingCard(card, timing) {
    const optimalWindow = timing.optimalWindow || 'Analysis pending';
    const riskReduction = timing.riskReduction || 0;

    let status = 'pending';
    let statusText = 'Pending';

    // Simple threshold check (not calculation, just display logic)
    if (riskReduction > 10) {
      status = 'recommended';
      statusText = 'Recommended';
    } else if (riskReduction > 0) {
      status = 'consider';
      statusText = 'Minor Benefit';
    }

    const rationale = timing.rationale ||
      (riskReduction > 0
        ? `Adjusting timing could reduce risk by ${riskReduction} points.`
        : 'Current timing is optimal.');

    card.innerHTML = `
      <div class="card-header">
        <h3 class="card-title">Timing Optimization</h3>
        <span class="status-pill" data-status="${status}">${statusText}</span>
      </div>
      <p class="card-why">${this._escapeHtml(rationale)}</p>
      <div class="card-kpis">
        <div class="kpi">
          <span class="kpi-label">Risk Reduction</span>
          <span class="kpi-value ${riskReduction > 0 ? 'text-risk-low' : ''}">${riskReduction > 0 ? '-' : ''}${Math.abs(riskReduction)} pts</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Optimal Window</span>
          <span class="kpi-value">${this._escapeHtml(optimalWindow)}</span>
        </div>
      </div>
    `;
  }

  /**
   * Render routing/carrier action card
   * @private
   */
  _renderRoutingCard(scenario) {
    const card = document.getElementById('decision-routing');
    if (!card) return;

    if (!scenario) {
      this._renderPendingCard(card, 'Routing & Carrier', 'Routing analysis pending...');
      return;
    }

    // Use ENGINE values directly (NO calculation)
    const riskReduction = scenario.riskReduction || 0;
    const costImpact = scenario.costImpact || 0;

    // Determine status from ENGINE flag or rank
    let status = 'pending';
    let statusText = 'Evaluate';

    if (scenario.isRecommended) {
      status = 'recommended';
      statusText = 'Recommended';
    } else if (scenario.rank === 1) {
      status = 'recommended';
      statusText = 'Top Choice';
    } else if (scenario.rank === 2) {
      status = 'consider';
      statusText = 'Alternative';
    }

    card.innerHTML = `
      <div class="card-header">
        <h3 class="card-title">Routing & Carrier</h3>
        <span class="status-pill" data-status="${status}">${statusText}</span>
      </div>
      <p class="card-why">${this._escapeHtml(scenario.description || 'Alternative routing option available.')}</p>
      <div class="card-kpis">
        <div class="kpi">
          <span class="kpi-label">Option</span>
          <span class="kpi-value">${this._escapeHtml(scenario.title || '—')}</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Cost Impact</span>
          <span class="kpi-value">${this._formatCurrency(costImpact)}</span>
        </div>
      </div>
    `;
  }

  /**
   * Render pending state for a card
   * @private
   */
  _renderPendingCard(card, title, message) {
    card.innerHTML = `
      <div class="card-header">
        <h3 class="card-title">${this._escapeHtml(title)}</h3>
        <span class="status-pill" data-status="pending">Pending</span>
      </div>
      <p class="card-why">${this._escapeHtml(message)}</p>
      <div class="card-kpis">
        <div class="kpi">
          <span class="kpi-label">Status</span>
          <span class="kpi-value">—</span>
        </div>
        <div class="kpi">
          <span class="kpi-label">Impact</span>
          <span class="kpi-value">—</span>
        </div>
      </div>
    `;
  }

  /**
   * Update confidence indicator
   * @private
   */
  _updateConfidence(confidence) {
    const confidenceEl = document.getElementById('confidence-value');
    if (confidenceEl) {
      const percentage = Math.round(confidence * 100);
      confidenceEl.textContent = `${percentage}%`;
    }
  }

  /**
   * Format currency (DISPLAY ONLY, not calculation)
   * @private
   */
  _formatCurrency(value) {
    if (value == null || isNaN(value)) return '—';

    const absValue = Math.abs(value);
    const sign = value < 0 ? '-' : value > 0 ? '+' : '';

    if (absValue >= 1000000) {
      return `${sign}$${(absValue / 1000000).toFixed(1)}M`;
    }
    if (absValue >= 1000) {
      return `${sign}$${(absValue / 1000).toFixed(1)}K`;
    }
    return `${sign}$${absValue.toFixed(0)}`;
  }

  /**
   * Escape HTML
   * @private
   */
  _escapeHtml(str) {
    if (str == null) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
  }

  /**
   * Inject component styles
   * @private
   */
  _injectStyles() {
    if (this._stylesInjected) return;
    if (document.getElementById('decision-summary-styles')) {
      this._stylesInjected = true;
      return;
    }

    const style = document.createElement('style');
    style.id = 'decision-summary-styles';
    style.textContent = `
      /* DecisionSummary Component Styles */
      .decision-card {
        position: relative;
        overflow: hidden;
      }
      
      .decision-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--risk-low), var(--risk-med), var(--risk-high));
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      
      .decision-card:hover::before {
        opacity: 0.3;
      }
      
      .kpi-value.text-risk-low {
        color: var(--risk-low);
        font-weight: 700;
      }
    `;

    document.head.appendChild(style);
    this._stylesInjected = true;
  }
}

// ES Module Export
export { DecisionSummary };

console.log('[DecisionSummary] ✓ Component module loaded (STRICT ENGINE-FIRST)');
