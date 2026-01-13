/**
 * RiskFanChart Component
 * 
 * Displays risk uncertainty over time using percentile projections (P10, P50, P90).
 * Creates a "fan" effect showing the range of possible outcomes.
 * 
 * ENGINE-FIRST ARCHITECTURE:
 * - All projection data comes PRE-CALCULATED from engine
 * - Component only renders the data, NO calculations
 * - Uses Chart.js for visualization
 * 
 * REQUIRED ENGINE DATA:
 * {
 *   riskScenarioProjections: [
 *     {
 *       date: "2025-01-08",  // ISO date string
 *       p10: 28,             // 10th percentile (best case)
 *       p50: 42,             // 50th percentile (expected)
 *       p90: 56,             // 90th percentile (worst case)
 *       phase: "Booking"     // Optional phase label
 *     }
 *   ],
 *   shipment: {
 *     etd: "2025-01-08",
 *     eta: "2025-02-15"
 *   }
 * }
 */

class RiskFanChart {
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
            console.warn('[RiskFanChart] No container element provided');
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
            console.warn('[RiskFanChart] Component not mounted');
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
        const projections = data.riskScenarioProjections || data.projections || [];
        const etd = data.shipment?.etd || data.etd;
        const eta = data.shipment?.eta || data.eta;

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        // Check for data
        if (!projections || projections.length === 0) {
            this._renderEmptyState();
            return;
        }

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.id = 'risk-fan-chart-canvas';
        this.container.innerHTML = '';
        this.container.appendChild(canvas);

        // Prepare data for Chart.js
        const labels = projections.map(p => this._formatDate(p.date));
        const p10Data = projections.map(p => p.p10);
        const p50Data = projections.map(p => p.p50);
        const p90Data = projections.map(p => p.p90);

        // Create chart
        const ctx = canvas.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    // P90 (worst case) - filled area
                    {
                        label: 'Worst Case (P90)',
                        data: p90Data,
                        borderColor: 'rgba(239, 68, 68, 0.8)',
                        backgroundColor: 'rgba(239, 68, 68, 0.15)',
                        borderWidth: 2,
                        fill: '+1',
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    },
                    // P50 (expected) - line only
                    {
                        label: 'Expected (P50)',
                        data: p50Data,
                        borderColor: 'rgba(96, 165, 250, 1)',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        pointBackgroundColor: 'rgba(96, 165, 250, 1)'
                    },
                    // P10 (best case) - filled area
                    {
                        label: 'Best Case (P10)',
                        data: p10Data,
                        borderColor: 'rgba(16, 185, 129, 0.8)',
                        backgroundColor: 'rgba(16, 185, 129, 0.15)',
                        borderWidth: 2,
                        fill: 'origin',
                        tension: 0.4,
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
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
                        backgroundColor: 'rgba(20, 20, 30, 0.9)',
                        titleColor: 'rgba(255, 255, 255, 0.95)',
                        bodyColor: 'rgba(255, 255, 255, 0.85)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            title: (context) => {
                                const index = context[0].dataIndex;
                                const projection = projections[index];
                                return projection.phase
                                    ? `${context[0].label} (${projection.phase})`
                                    : context[0].label;
                            },
                            label: (context) => {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.6)',
                            font: {
                                size: 10
                            },
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.6)',
                            font: {
                                size: 11
                            },
                            callback: (value) => `${value}`
                        },
                        title: {
                            display: true,
                            text: 'Risk Score',
                            color: 'rgba(255, 255, 255, 0.7)',
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Render empty state
     * @private
     */
    _renderEmptyState() {
        this.container.innerHTML = `
      <div class="chart-empty-state">
        <div class="empty-icon">📈</div>
        <p class="empty-text">No scenario projection data available</p>
      </div>
    `;
    }

    /**
     * Format date for display
     * @private
     */
    _formatDate(dateStr) {
        if (!dateStr) return '';

        try {
            const date = new Date(dateStr);
            const month = date.toLocaleDateString('en-US', { month: 'short' });
            const day = date.getDate();
            return `${month} ${day}`;
        } catch (e) {
            return dateStr;
        }
    }

    /**
     * Inject component styles
     * @private
     */
    _injectStyles() {
        if (this._stylesInjected) return;
        if (document.getElementById('risk-fan-chart-styles')) {
            this._stylesInjected = true;
            return;
        }

        const style = document.createElement('style');
        style.id = 'risk-fan-chart-styles';
        style.textContent = `
      /* RiskFanChart Component Styles */
      #risk-fan-chart-canvas {
        max-height: 320px;
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
export { RiskFanChart };

console.log('[RiskFanChart] ✓ Component module loaded');
