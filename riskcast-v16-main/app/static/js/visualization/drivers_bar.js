
(function() {
    'use strict';

    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.visualization === 'undefined') {
        window.RISKCAST.visualization = {};
    }

    const utils = window.RISKCAST.visualization.utils || {};

    /**
     * Factor labels
     */
    const FACTOR_LABELS = {
        delay: 'Delay Risk',
        port: 'Port Congestion',
        climate: 'Weather Hazard',
        carrier: 'Carrier Reliability',
        esg: 'ESG Exposure',
        equipment: 'Equipment Availability'
    };

    /**
     * Create driver bar chart
     */
    function createDriverBarChart(containerId, riskFactors) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Driver bar chart container not found: ${containerId}`);
            return null;
        }

        // Clear container
        container.innerHTML = '';

        // Create canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);

        // Sort factors by value (descending)
        const sortedFactors = Object.entries(riskFactors)
            .map(([key, value]) => ({
                key,
                label: FACTOR_LABELS[key] || key,
                value: value || 0
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 6); // Top 6

        const labels = sortedFactors.map(f => f.label);
        const values = sortedFactors.map(f => f.value);

        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            container.innerHTML = '<div class="viz-loading">Loading Chart.js...</div>';
            
            // Load Chart.js dynamically
            loadChartJS().then(() => {
                createDriverBarChart(containerId, riskFactors);
            });
            return null;
        }

        // Create gradient
        const gradient = createGradient(canvas);

        // Create chart
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Risk Influence',
                    data: values,
                    backgroundColor: gradient,
                    borderColor: '#00FFC8',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(2, 7, 7, 0.95)',
                        titleColor: '#00FFC8',
                        bodyColor: '#ffffff',
                        borderColor: '#00FFC8',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                return 'Risk: ' + (context.parsed.x * 100).toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        max: 1,
                        grid: {
                            color: 'rgba(0, 255, 200, 0.2)'
                        },
                        ticks: {
                            color: '#8FFFD0',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#00FFC8',
                            font: {
                                size: 12,
                                weight: 500
                            }
                        }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });

        return chart;
    }

    /**
     * Create gradient for bars
     */
    function createGradient(canvas) {
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#00FFC8');
        gradient.addColorStop(1, '#0080FF');
        return gradient;
    }

    /**
     * Load Chart.js dynamically
     */
    function loadChartJS() {
        return new Promise((resolve, reject) => {
            if (typeof Chart !== 'undefined') {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    /**
     * Update driver bar chart
     */
    function updateDriverBarChart(chart, riskFactors) {
        if (!chart) return;

        // Sort and update
        const sortedFactors = Object.entries(riskFactors)
            .map(([key, value]) => ({
                key,
                label: FACTOR_LABELS[key] || key,
                value: value || 0
            }))
            .sort((a, b) => b.value - a.value)
            .slice(0, 6);

        chart.data.labels = sortedFactors.map(f => f.label);
        chart.data.datasets[0].data = sortedFactors.map(f => f.value);
        chart.update('active');
    }

    // Export API
    window.RISKCAST.visualization.driversBar = {
        create: createDriverBarChart,
        update: updateDriverBarChart,
    };

    console.log('✅ RISKCAST Driver bar chart initialized');

})();





















