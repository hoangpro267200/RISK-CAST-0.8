
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
     * Risk factor labels
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
     * Create radar chart using Chart.js
     */
    function createRadarChart(containerId, riskFactors) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Radar chart container not found: ${containerId}`);
            return null;
        }

        // Clear container
        container.innerHTML = '';

        // Create canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);

        // Prepare data
        const labels = [];
        const values = [];

        // Order: delay, port, climate, carrier, esg, equipment
        const orderedFactors = ['delay', 'port', 'climate', 'carrier', 'esg', 'equipment'];
        
        orderedFactors.forEach(factor => {
            labels.push(FACTOR_LABELS[factor] || factor);
            values.push(riskFactors[factor] || 0);
        });

        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            container.innerHTML = '<div class="viz-loading">Loading Chart.js...</div>';
            
            // Load Chart.js dynamically
            loadChartJS().then(() => {
                createRadarChart(containerId, riskFactors);
            });
            return null;
        }

        // Create chart
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Risk Factors',
                    data: values,
                    backgroundColor: 'rgba(0, 255, 200, 0.15)',
                    borderColor: '#00FFC8',
                    borderWidth: 2,
                    pointBackgroundColor: '#00FFC8',
                    pointBorderColor: '#00FFC8',
                    pointHoverBackgroundColor: '#0080FF',
                    pointHoverBorderColor: '#00FFC8',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 1,
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
                                return context.label + ': ' + (context.parsed.r * 100).toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 1,
                        min: 0,
                        ticks: {
                            stepSize: 0.2,
                            color: '#8FFFD0',
                            font: {
                                size: 11
                            },
                            callback: function(value) {
                                return (value * 100) + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(0, 255, 200, 0.2)'
                        },
                        pointLabels: {
                            color: '#00FFC8',
                            font: {
                                size: 12,
                                weight: 500
                            }
                        },
                        angleLines: {
                            color: 'rgba(0, 255, 200, 0.2)'
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
     * Update radar chart with new data
     */
    function updateRadarChart(chart, riskFactors) {
        if (!chart) return;

        const orderedFactors = ['delay', 'port', 'climate', 'carrier', 'esg', 'equipment'];
        const values = orderedFactors.map(factor => riskFactors[factor] || 0);

        chart.data.datasets[0].data = values;
        chart.update('active');
    }

    // Export API
    window.RISKCAST.visualization.radar = {
        create: createRadarChart,
        update: updateRadarChart,
    };

    console.log('✅ RISKCAST Radar chart initialized');

})();





















