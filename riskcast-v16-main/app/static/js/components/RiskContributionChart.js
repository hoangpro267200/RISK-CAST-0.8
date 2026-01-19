/**
 * RiskContributionChart Component
 * 
 * Displays risk layer contributions as a horizontal bar chart.
 * Shows how each layer contributes to the overall risk score.
 * 
 * ENGINE-FIRST ARCHITECTURE:
 * - All contribution percentages come PRE-CALCULATED from engine
 * - Component only renders the data, NO calculations
 * - Uses Chart.js horizontal bar chart
 * 
 * REQUIRED ENGINE DATA:
 * {
 *   layers: [
 *     {
 *       name: "Transport Risk",
 *       score: 72,              // Pre-computed by engine
 *       contribution: 28,       // Pre-computed percentage (0-100)
 *       status: "WARNING",      // Engine classification
 *       confidence: 85          // Optional data quality
 *     }
 *   ],
 *   overallScore: 68  // Overall risk score for reference
 * }
 */

class RiskContributionChart {
    constructor() {
        this.container = null;
        this.chart = null;
        this._stylesInjected = false;
    }

    /**
     * Mount component to DOM
     * @param {HTMLElement} el - Container element
     * @param {Object} data - Chart data from engine
     */
    mount(el, data = {}) {
        if (!el) {
            console.warn('[RiskContributionChart] No container element provided');
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
            console.warn('[RiskContributionChart] Component not mounted');
            return;
        }

        this._render(data);
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
        const layers = data.layers || [];
        const overallScore = data.overallScore || 0;

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        // Check for data
        if (!layers || layers.length === 0) {
            this._renderEmptyState();
            return;
        }

        // Sort layers by contribution (descending)
        const sortedLayers = [...layers].sort((a, b) =>
            (b.contribution || 0) - (a.contribution || 0)
        );

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.id = 'risk-contribution-canvas';
        this.container.innerHTML = '';
        this.container.appendChild(canvas);

        // Prepare data
        const labels = sortedLayers.map(l => l.name);
        const contributions = sortedLayers.map(l => l.contribution || 0);
        const backgroundColors = sortedLayers.map(l => this._getLayerColor(l.score, l.status));
        const borderColors = sortedLayers.map(l => this._getLayerBorderColor(l.score, l.status));

        // Create chart
        const ctx = canvas.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Contribution (%)',
                    data: contributions,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', // Horizontal bars
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(20, 20, 30, 0.95)',
                        titleColor: 'rgba(255, 255, 255, 0.95)',
                        bodyColor: 'rgba(255, 255, 255, 0.85)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            title: (context) => {
                                const index = context[0].dataIndex;
                                const layer = sortedLayers[index];
                                return layer.name;
                            },
                            label: (context) => {
                                const index = context.dataIndex;
                                const layer = sortedLayers[index];

                                return [
                                    `Contribution: ${layer.contribution}%`,
                                    `Risk Score: ${layer.score}/100`,
                                    `Status: ${layer.status || 'N/A'}`,
                                    layer.confidence ? `Confidence: ${layer.confidence}%` : ''
                                ].filter(Boolean);
                            },
                            afterLabel: (context) => {
                                const index = context.dataIndex;
                                const layer = sortedLayers[index];

                                if (layer.notes) {
                                    return `\n${layer.notes}`;
                                }
                                return '';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.6)',
                            font: {
                                size: 10
                            },
                            callback: (value) => `${value}%`
                        },
                        title: {
                            display: true,
                            text: 'Contribution to Overall Risk (%)',
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });

        // Add summary footer
        this._addSummaryFooter(sortedLayers, overallScore);
    }

    /**
     * Add summary footer with total contribution
     * @private
     */
    _addSummaryFooter(layers, overallScore) {
        const totalContribution = layers.reduce((sum, l) => sum + (l.contribution || 0), 0);
        const avgConfidence = layers.reduce((sum, l) => sum + (l.confidence || 0), 0) / layers.length;

        const footer = document.createElement('div');
        footer.className = 'contribution-summary';
        footer.innerHTML = `
      <div class="summary-item">
        <span class="summary-label">Total Layers:</span>
        <span class="summary-value">${layers.length}</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">Total Contribution:</span>
        <span class="summary-value">${totalContribution.toFixed(1)}%</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">Overall Risk:</span>
        <span class="summary-value">${overallScore}/100</span>
      </div>
      ${avgConfidence > 0 ? `
      <div class="summary-item">
        <span class="summary-label">Avg Confidence:</span>
        <span class="summary-value">${avgConfidence.toFixed(1)}%</span>
      </div>
      ` : ''}
    `;

        this.container.appendChild(footer);
    }

    /**
     * Get layer color based on score and status
     * @private
     */
    _getLayerColor(score, status) {
        // Use status if available (engine classification)
        if (status) {
            const statusUpper = status.toUpperCase();
            if (statusUpper === 'ALERT') return 'rgba(239, 68, 68, 0.6)';
            if (statusUpper === 'WARNING') return 'rgba(245, 158, 11, 0.6)';
            if (statusUpper === 'NORMAL') return 'rgba(16, 185, 129, 0.6)';
        }

        // Fallback to score-based coloring (display logic only)
        if (score >= 70) return 'rgba(239, 68, 68, 0.6)';
        if (score >= 40) return 'rgba(245, 158, 11, 0.6)';
        return 'rgba(16, 185, 129, 0.6)';
    }

    /**
     * Get layer border color
     * @private
     */
    _getLayerBorderColor(score, status) {
        // Use status if available
        if (status) {
            const statusUpper = status.toUpperCase();
            if (statusUpper === 'ALERT') return 'rgba(239, 68, 68, 1)';
            if (statusUpper === 'WARNING') return 'rgba(245, 158, 11, 1)';
            if (statusUpper === 'NORMAL') return 'rgba(16, 185, 129, 1)';
        }

        // Fallback to score-based
        if (score >= 70) return 'rgba(239, 68, 68, 1)';
        if (score >= 40) return 'rgba(245, 158, 11, 1)';
        return 'rgba(16, 185, 129, 1)';
    }

    /**
     * Render empty state
     * @private
     */
    _renderEmptyState() {
        this.container.innerHTML = `
      <div class="chart-empty-state">
        <div class="empty-icon">📊</div>
        <p class="empty-text">No layer contribution data available</p>
      </div>
    `;
    }

    /**
     * Inject component styles
     * @private
     */
    _injectStyles() {
        if (this._stylesInjected) return;
        if (document.getElementById('risk-contribution-styles')) {
            this._stylesInjected = true;
            return;
        }

        const style = document.createElement('style');
        style.id = 'risk-contribution-styles';
        style.textContent = `
      /* RiskContributionChart Component Styles */
      #risk-contribution-canvas {
        max-height: 320px;
      }
      
      .contribution-summary {
        display: flex;
        justify-content: space-around;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 1rem;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
      }
      
      .summary-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.25rem;
      }
      
      .summary-label {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      
      .summary-value {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
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
export { RiskContributionChart };

console.log('[RiskContributionChart] ✓ Component module loaded');
