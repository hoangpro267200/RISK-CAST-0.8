
(function() {
    'use strict';

    // RISKCAST visualization namespace
    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.visualization === 'undefined') {
        window.RISKCAST.visualization = {};
    }

    /**
     * Color palette (neon theme)
     */
    const COLORS = {
        neonGreen: '#00FFC8',
        neonCyan: '#00D9FF',
        neonBlue: '#0080FF',
        neonYellow: '#FFD700',
        neonOrange: '#FF6B35',
        neonRed: '#FF3366',
        neonPink: '#FF00FF',
        
        // Gradients
        gradientLow: 'linear-gradient(135deg, #00FFC8 0%, #0080FF 100%)',
        gradientMedium: 'linear-gradient(135deg, #FFD700 0%, #FF6B35 100%)',
        gradientHigh: 'linear-gradient(135deg, #FF3366 0%, #FF00FF 100%)',
        
        // Background
        bgDark: '#020707',
        bgCard: 'rgba(5, 59, 52, 0.15)',
    };

    /**
     * Get risk color based on score (0-1)
     */
    function getRiskColor(score) {
        if (score < 0.33) {
            return COLORS.neonGreen;
        } else if (score < 0.67) {
            return COLORS.neonYellow;
        } else {
            return COLORS.neonRed;
        }
    }

    /**
     * Get risk gradient based on score
     */
    function getRiskGradient(score) {
        if (score < 0.33) {
            return COLORS.gradientLow;
        } else if (score < 0.67) {
            return COLORS.gradientMedium;
        } else {
            return COLORS.gradientHigh;
        }
    }

    /**
     * Format percentage
     */
    function formatPercent(value, decimals = 1) {
        return (value * 100).toFixed(decimals) + '%';
    }

    /**
     * Format number with commas
     */
    function formatNumber(value) {
        return value.toLocaleString('en-US');
    }

    /**
     * Debounce function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle function
     */
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Create canvas context with high DPI support
     */
    function getHighDPICanvas(canvas) {
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        canvas.style.width = rect.width + 'px';
        canvas.style.height = rect.height + 'px';
        
        return ctx;
    }

    /**
     * Smooth animation helper
     */
    function animateValue(start, end, duration, callback) {
        const startTime = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out)
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = start + (end - start) * eased;
            
            callback(value);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }

    /**
     * Check if element is in viewport (for lazy loading)
     */
    function isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    /**
     * Lazy load chart when in viewport
     */
    function lazyLoadChart(observer, element, initFunction) {
        const observerInstance = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    initFunction();
                    observerInstance.unobserve(entry.target);
                }
            });
        }, { rootMargin: '50px' });
        
        observerInstance.observe(element);
        return observerInstance;
    }

    /**
     * Export chart as base64 PNG image
     * Supports Chart.js, Plotly, and canvas-based charts
     */
    function exportChartAsBase64(chartInstanceOrElement) {
        return new Promise((resolve, reject) => {
            try {
                // Case 1: Chart.js instance
                if (chartInstanceOrElement && chartInstanceOrElement.canvas) {
                    const canvas = chartInstanceOrElement.canvas;
                    const base64 = canvas.toDataURL('image/png');
                    resolve(base64);
                    return;
                }
                
                // Case 2: Plotly chart (element ID or element)
                if (typeof Plotly !== 'undefined') {
                    const element = typeof chartInstanceOrElement === 'string' 
                        ? document.getElementById(chartInstanceOrElement)
                        : chartInstanceOrElement;
                    
                    if (element) {
                        Plotly.toImage(element, {
                            format: 'png',
                            width: element.clientWidth || 800,
                            height: element.clientHeight || 600,
                            scale: 2  // Higher resolution
                        }).then((dataUrl) => {
                            resolve(dataUrl);
                        }).catch(reject);
                        return;
                    }
                }
                
                // Case 3: Canvas element
                if (chartInstanceOrElement instanceof HTMLCanvasElement) {
                    const base64 = chartInstanceOrElement.toDataURL('image/png');
                    resolve(base64);
                    return;
                }
                
                // Case 4: Container with canvas child
                if (chartInstanceOrElement instanceof HTMLElement) {
                    const canvas = chartInstanceOrElement.querySelector('canvas');
                    if (canvas) {
                        const base64 = canvas.toDataURL('image/png');
                        resolve(base64);
                        return;
                    }
                    
                    // Try to find Plotly div
                    const plotlyDiv = chartInstanceOrElement.querySelector('.plotly');
                    if (plotlyDiv && typeof Plotly !== 'undefined') {
                        Plotly.toImage(plotlyDiv, {
                            format: 'png',
                            width: plotlyDiv.clientWidth || 800,
                            height: plotlyDiv.clientHeight || 600,
                            scale: 2
                        }).then(resolve).catch(reject);
                        return;
                    }
                }
                
                // Case 5: Chart.js by container ID
                if (typeof chartInstanceOrElement === 'string') {
                    const container = document.getElementById(chartInstanceOrElement);
                    if (!container) {
                        reject(new Error(`Element not found: ${chartInstanceOrElement}`));
                        return;
                    }
                    
                    // Try to find Chart.js canvas
                    const canvas = container.querySelector('canvas');
                    if (canvas) {
                        // Try to get Chart.js instance from Chart.instances
                        if (typeof Chart !== 'undefined' && Chart.getChart(canvas)) {
                            const chart = Chart.getChart(canvas);
                            const base64 = chart.canvas.toDataURL('image/png');
                            resolve(base64);
                            return;
                        }
                        
                        // Just export canvas
                        const base64 = canvas.toDataURL('image/png');
                        resolve(base64);
                        return;
                    }
                    
                    // Try Plotly
                    if (typeof Plotly !== 'undefined' && container.querySelector('.plotly')) {
                        const plotlyDiv = container.querySelector('.plotly');
                        Plotly.toImage(plotlyDiv, {
                            format: 'png',
                            width: plotlyDiv.clientWidth || 800,
                            height: plotlyDiv.clientHeight || 600,
                            scale: 2
                        }).then(resolve).catch(reject);
                        return;
                    }
                }
                
                reject(new Error('Unsupported chart type or element'));
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Export all charts on the page
     */
    async function exportAllCharts() {
        const charts = {};
        
        // Radar chart
        const radarContainer = document.getElementById('radar-chart') || 
                              document.querySelector('[id*="radar"]');
        if (radarContainer) {
            try {
                charts.radar = await exportChartAsBase64(radarContainer);
            } catch (e) {
                console.warn('[Chart Export] Failed to export radar:', e);
            }
        }
        
        // Heatmap
        const heatmapContainer = document.getElementById('heatmap-container') ||
                                document.querySelector('[id*="heatmap"]');
        if (heatmapContainer) {
            try {
                charts.heatmap = await exportChartAsBase64(heatmapContainer);
            } catch (e) {
                console.warn('[Chart Export] Failed to export heatmap:', e);
            }
        }
        
        // Drivers bar chart
        const driversContainer = document.getElementById('drivers-bar-chart') ||
                                document.querySelector('[id*="driver"]');
        if (driversContainer) {
            try {
                charts.drivers_bar = await exportChartAsBase64(driversContainer);
            } catch (e) {
                console.warn('[Chart Export] Failed to export drivers:', e);
            }
        }
        
        // Timeline
        const timelineContainer = document.getElementById('timeline-chart') ||
                                 document.querySelector('[id*="timeline"]');
        if (timelineContainer) {
            try {
                charts.timeline = await exportChartAsBase64(timelineContainer);
            } catch (e) {
                console.warn('[Chart Export] Failed to export timeline:', e);
            }
        }
        
        // Network graph
        const networkContainer = document.getElementById('network-graph') ||
                                document.querySelector('[id*="network"]');
        if (networkContainer) {
            try {
                charts.network = await exportChartAsBase64(networkContainer);
            } catch (e) {
                console.warn('[Chart Export] Failed to export network:', e);
            }
        }
        
        // Gauge
        const gaugeContainer = document.getElementById('confidence-gauge') ||
                              document.querySelector('[id*="gauge"]');
        if (gaugeContainer) {
            try {
                charts.gauge = await exportChartAsBase64(gaugeContainer);
            } catch (e) {
                console.warn('[Chart Export] Failed to export gauge:', e);
            }
        }
        
        return charts;
    }

    // Export utilities
    window.RISKCAST.visualization.utils = {
        COLORS,
        getRiskColor,
        getRiskGradient,
        formatPercent,
        formatNumber,
        debounce,
        throttle,
        getHighDPICanvas,
        animateValue,
        isInViewport,
        lazyLoadChart,
        exportChartAsBase64,
        exportAllCharts,
    };

    console.log('✅ RISKCAST Visualization Utilities initialized');

})();


