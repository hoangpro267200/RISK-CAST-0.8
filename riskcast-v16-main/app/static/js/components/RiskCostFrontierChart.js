/**
 * RiskCostFrontierChart Component
 * 
 * Displays risk reduction vs. cost trade-offs for available mitigation strategies.
 * Shows Pareto frontier to identify efficient scenarios.
 * 
 * ENGINE-FIRST ARCHITECTURE:
 * - All scenario values (riskReduction, costImpact) come from engine
 * - Component only renders the data, NO calculations
 * - Uses Chart.js scatter plot
 * 
 * REQUIRED ENGINE DATA:
 * {
 *   scenarios: [
 *     {
 *       id: "scenario-1",
 *       title: "Add Insurance",
 *       riskReduction: 0,      // Pre-computed by engine
 *       costImpact: 1250,      // Pre-computed by engine
 *       isRecommended: true,   // Optional engine flag
 *       rank: 1                // Optional engine ranking
 *     }
 *   ],
 *   baselineRisk: 68  // Current risk score
 * }
 */

class RiskCostFrontierChart {
    constructor() {
        this.container = null;
        this.chart = null;
        this.highlightedScenario = null;
        this._stylesInjected = false;
    }

    /**
     * Mount component to DOM
     * @param {HTMLElement} el - Container element
     * @param {Object} data - Chart data from engine
     */
    mount(el, data = {}) {
        if (!el) {
            console.warn('[RiskCostFrontierChart] No container element provided');
            return;
        }

        this.container = el;
        this._injectStyles();
        this._render(data);
    }

    /**
     * Update component with new data
     * @param {Object} data - Updated chart data
     */
    update(data = {}) {
        if (!this.container) {
            console.warn('[RiskCostFrontierChart] Component not mounted');
            return;
        }

        this._render(data);
    }

    /**
     * Highlight a specific scenario
     * @param {string} scenarioTitle - Title of scenario to highlight
     */
    highlight(scenarioTitle) {
        this.highlightedScenario = scenarioTitle;
        if (this.chart) {
            this.chart.update();
        }
    }

    /**
     * Destroy component and cleanup
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        this.container = null;
    }

    /**
     * Render chart
     * @private
     */
    _render(data) {
        const scenarios = data.scenarios || [];
        const baselineRisk = data.baselineRisk || 0;
        const highlightedScenario = data.highlightedScenario || this.highlightedScenario;

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        // Check for data
        if (!scenarios || scenarios.length === 0) {
            this._renderEmptyState();
            return;
        }

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.id = 'risk-cost-frontier-canvas';
        this.container.innerHTML = '';
        this.container.appendChild(canvas);

        // Prepare data points
        // X-axis: Cost Impact (negative = savings, positive = cost)
        // Y-axis: Risk Reduction (negative = increase, positive = reduction)
        const dataPoints = scenarios.map(s => ({
            x: s.costImpact || 0,
            y: s.riskReduction || 0,
            scenario: s
        }));

        // Separate recommended vs others
        const recommended = dataPoints.filter(p => p.scenario.isRecommended || p.scenario.rank === 1);
        const others = dataPoints.filter(p => !p.scenario.isRecommended && p.scenario.rank !== 1);
        const highlighted = highlightedScenario
            ? dataPoints.filter(p => p.scenario.title === highlightedScenario)
            : [];

        // Create chart
        const ctx = canvas.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [
                    // Highlighted scenario (if any)
                    ...(highlighted.length > 0 ? [{
                        label: 'Selected',
                        data: highlighted,
                        backgroundColor: 'rgba(139, 92, 246, 0.8)',
                        borderColor: 'rgba(139, 92, 246, 1)',
                        borderWidth: 3,
                        pointRadius: 10,
                        pointHoverRadius: 12,
                        pointStyle: 'star'
                    }] : []),
                    // Recommended scenarios
                    ...(recommended.length > 0 ? [{
                        label: 'Recommended',
                        data: recommended,
                        backgroundColor: 'rgba(16, 185, 129, 0.7)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 2,
                        pointRadius: 8,
                        pointHoverRadius: 10
                    }] : []),
                    // Other scenarios
                    {
                        label: 'Alternative',
                        data: others,
                        backgroundColor: 'rgba(96, 165, 250, 0.5)',
                        borderColor: 'rgba(96, 165, 250, 0.8)',
                        borderWidth: 2,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'point',
                    intersect: true
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                size: 11
                            },
                            padding: 15,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(20, 20, 30, 0.95)',
                        titleColor: 'rgba(255, 255, 255, 0.95)',
                        bodyColor: 'rgba(255, 255, 255, 0.85)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            title: (context) => {
                                const point = context[0].raw;
                                return point.scenario.title || 'Scenario';
                            },
                            label: (context) => {
                                const point = context.raw;
                                const riskChange = point.y;
                                const cost = point.x;

                                return [
                                    `Risk Change: ${riskChange > 0 ? '-' : '+'}${Math.abs(riskChange)} pts`,
                                    `Cost Impact: ${this._formatCurrency(cost)}`,
                                    point.scenario.description ? `${point.scenario.description}` : ''
                                ].filter(Boolean);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.6)',
                            font: {
                                size: 10
                            },
                            callback: (value) => this._formatCurrency(value)
                        },
                        title: {
                            display: true,
                            text: 'Cost Impact (USD)',
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                size: 12
                            }
                        }
                    },
                    y: {
                        type: 'linear',
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.6)',
                            font: {
                                size: 10
                            },
                            callback: (value) => `${value > 0 ? '-' : '+'}${Math.abs(value)}`
                        },
                        title: {
                            display: true,
                            text: 'Risk Reduction (points)',
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });

        // Add quadrant labels
        this._addQuadrantLabels();
    }

    /**
     * Add quadrant labels to help interpret the chart
     * @private
     */
    _addQuadrantLabels() {
        const labelsContainer = document.createElement('div');
        labelsContainer.className = 'frontier-quadrant-labels';
        labelsContainer.innerHTML = `
      <div class="quadrant-label top-left">
        <span class="label-icon">✓</span>
        <span class="label-text">Best: Lower Cost + Lower Risk</span>
      </div>
      <div class="quadrant-label bottom-right">
        <span class="label-icon">✗</span>
        <span class="label-text">Worst: Higher Cost + Higher Risk</span>
      </div>
    `;

        this.container.appendChild(labelsContainer);
    }

    /**
     * Render empty state
     * @private
     */
    _renderEmptyState() {
        this.container.innerHTML = `
      <div class="chart-empty-state">
        <div class="empty-icon">📊</div>
        <p class="empty-text">No mitigation scenarios available</p>
      </div>
    `;
    }

    /**
     * Format currency (DISPLAY ONLY)
     * @private
     */
    _formatCurrency(value) {
        if (value == null || isNaN(value)) return '$0';

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
     * Inject component styles
     * @private
     */
    _injectStyles() {
        if (this._stylesInjected) return;
        if (document.getElementById('risk-cost-frontier-styles')) {
            this._stylesInjected = true;
            return;
        }

        const style = document.createElement('style');
        style.id = 'risk-cost-frontier-styles';
        style.textContent = `
      /* RiskCostFrontierChart Component Styles */
      #risk-cost-frontier-canvas {
        max-height: 320px;
      }
      
      .frontier-quadrant-labels {
        display: flex;
        justify-content: space-between;
        margin-top: 1rem;
        padding: 0 1rem;
        font-size: 0.75rem;
      }
      
      .quadrant-label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-muted);
      }
      
      .quadrant-label.top-left .label-icon {
        color: var(--risk-low);
      }
      
      .quadrant-label.bottom-right .label-icon {
        color: var(--risk-high);
      }
      
      .label-text {
        font-size: 0.75rem;
      }
      
      .chart-empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 320px;
        color: var(--text-muted);
      }
      
      .chart-empty-state .empty-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
      }
      
      .chart-empty-state .empty-text {
        font-size: 0.875rem;
      }
    `;

        document.head.appendChild(style);
        this._stylesInjected = true;
    }
}

// ES Module Export
export { RiskCostFrontierChart };

console.log('[RiskCostFrontierChart] ✓ Component module loaded');
