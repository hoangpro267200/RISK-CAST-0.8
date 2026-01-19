
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
     * Create timeline chart
     */
    function createTimelineChart(containerId, timelineData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Timeline chart container not found: ${containerId}`);
            return null;
        }

        // Clear container
        container.innerHTML = '';

        // Create canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);

        // Prepare data
        const labels = timelineData.map(d => 'Day ' + d.day);
        const values = timelineData.map(d => d.score || 0);

        // Check if Chart.js is available
        if (typeof Chart === 'undefined') {
            container.innerHTML = '<div class="viz-loading">Loading Chart.js...</div>';
            
            // Load Chart.js dynamically
            loadChartJS().then(() => {
                createTimelineChart(containerId, timelineData);
            });
            return null;
        }

        // Create gradient for area fill
        const gradient = createAreaGradient(canvas);

        // Create chart
        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Risk Score',
                    data: values,
                    borderColor: '#00FFC8',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4, // Smooth bezier curve
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#00FFC8',
                    pointBorderColor: '#020707',
                    pointBorderWidth: 2,
                    pointHoverBackgroundColor: '#0080FF',
                    pointHoverBorderColor: '#00FFC8',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2.5,
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
                                return 'Risk: ' + (context.parsed.y * 100).toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(0, 255, 200, 0.2)'
                        },
                        ticks: {
                            color: '#8FFFD0',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
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
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                },
                elements: {
                    line: {
                        shadowColor: 'rgba(0, 255, 200, 0.5)',
                        shadowBlur: 10,
                        shadowOffsetY: 2
                    }
                }
            }
        });

        return chart;
    }

    /**
     * Create gradient for area fill
     */
    function createAreaGradient(canvas) {
        const ctx = canvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
        gradient.addColorStop(0, 'rgba(0, 255, 200, 0.4)');
        gradient.addColorStop(1, 'rgba(0, 255, 200, 0.05)');
        return gradient;
    }

    /**
     * Generate timeline data from risk score (if not provided)
     */
    function generateTimelineData(riskScore, days = 30) {
        const data = [];
        const baseScore = riskScore / 100; // Convert to 0-1
        
        for (let day = 1; day <= days; day++) {
            // Add some variation based on day
            const variation = Math.sin(day * 0.2) * 0.1;
            const trend = (day / days) * 0.15; // Slight upward trend
            const score = Math.max(0, Math.min(1, baseScore + variation + trend));
            
            data.push({
                day: day,
                score: score
            });
        }
        
        return data;
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
     * Update timeline chart
     */
    function updateTimelineChart(chart, timelineData) {
        if (!chart) return;

        const labels = timelineData.map(d => 'Day ' + d.day);
        const values = timelineData.map(d => d.score || 0);

        chart.data.labels = labels;
        chart.data.datasets[0].data = values;
        chart.update('active');
    }

    // Export API
    window.RISKCAST.visualization.timeline = {
        create: createTimelineChart,
        update: updateTimelineChart,
        generateTimelineData: generateTimelineData,
    };

    console.log('✅ RISKCAST Timeline chart initialized');

})();





















