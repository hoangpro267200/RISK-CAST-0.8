
(function() {
    'use strict';

    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.modules === 'undefined') {
        window.RISKCAST.modules = {};
    }

    const PDFExport = {
        /**
         * Initialize PDF export functionality
         */
        init: function() {
            const exportBtn = document.getElementById('exportPdfBtn');
            if (exportBtn) {
                exportBtn.addEventListener('click', () => this.exportPDF());
                console.log('[PDF Export] Initialized');
            } else {
                console.warn('[PDF Export] Export button not found');
            }
        },

        /**
         * Export PDF report
         */
        exportPDF: async function() {
            console.log('[PDF Export] Starting PDF export...');
            
            // Show loading state
            this.setLoadingState(true);
            
            try {
                // 1. Collect all chart images (base64)
                const charts = await this.collectCharts();
                console.log('[PDF Export] Charts collected:', Object.keys(charts));
                
                // 2. Collect risk assessment data
                const riskData = this.collectRiskData();
                console.log('[PDF Export] Risk data collected');
                
                // 3. Prepare report request
                const reportRequest = {
                    ...riskData,
                    charts: charts
                };
                
                // 4. Call API to generate PDF
                const response = await fetch('/api/v1/risk/v2/report/pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(reportRequest)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                // 5. Download PDF
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `riskcast_report_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                console.log('[PDF Export] PDF exported successfully');
                
            } catch (error) {
                console.error('[PDF Export] Error exporting PDF:', error);
                alert('Failed to export PDF: ' + error.message);
            } finally {
                this.setLoadingState(false);
            }
        },

        /**
         * Collect all chart images as base64
         */
        collectCharts: async function() {
            const charts = {};
            
            // Check if export utilities are available
            if (!window.RISKCAST || !window.RISKCAST.visualization || !window.RISKCAST.visualization.utils) {
                console.warn('[PDF Export] Visualization utilities not available');
                return charts;
            }
            
            const utils = window.RISKCAST.visualization.utils;
            
            // Export all charts using utility function
            if (utils.exportAllCharts) {
                try {
                    const exportedCharts = await utils.exportAllCharts();
                    return exportedCharts;
                } catch (error) {
                    console.error('[PDF Export] Error exporting charts:', error);
                }
            }
            
            // Fallback: try to export individual charts
            const chartSelectors = {
                radar: ['radar-chart', '[id*="radar"]'],
                heatmap: ['heatmap-container', '[id*="heatmap"]'],
                drivers_bar: ['drivers-bar-chart', '[id*="driver"]'],
                timeline: ['timeline-chart', '[id*="timeline"]'],
                network: ['network-graph', '[id*="network"]'],
                gauge: ['confidence-gauge', '[id*="gauge"]']
            };
            
            for (const [key, selectors] of Object.entries(chartSelectors)) {
                try {
                    let element = null;
                    for (const selector of selectors) {
                        if (selector.startsWith('#')) {
                            element = document.getElementById(selector.slice(1));
                        } else {
                            element = document.querySelector(selector);
                        }
                        if (element) break;
                    }
                    
                    if (element && utils.exportChartAsBase64) {
                        charts[key] = await utils.exportChartAsBase64(element);
                    }
                } catch (error) {
                    console.warn(`[PDF Export] Failed to export ${key}:`, error);
                }
            }
            
            return charts;
        },

        /**
         * Collect risk assessment data from ResultsCore
         */
        collectRiskData: function() {
            // Try to get data from ResultsCore
            let riskData = null;
            
            if (window.ResultsCore && window.ResultsCore.data) {
                riskData = window.ResultsCore.data.result || window.ResultsCore.data;
            }
            
            // Fallback: try to get from global data store
            if (!riskData && window.RISKCAST && window.RISKCAST.data) {
                riskData = window.RISKCAST.data;
            }
            
            // If no data found, create minimal structure
            if (!riskData) {
                console.warn('[PDF Export] No risk data found, using defaults');
                riskData = {
                    risk_score: 0,
                    risk_level: 'Unknown',
                    confidence: 0.5,
                    profile: {},
                    matrix: {},
                    factors: {},
                    drivers: [],
                    recommendations: []
                };
            }
            
            // Extract route from page
            const routeChip = document.getElementById('routeChip');
            const route = routeChip ? routeChip.textContent.trim() : 'Unknown Route';
            
            // Build report data structure
            const reportData = {
                risk_score: riskData.risk_score || riskData.overall_risk || 0,
                risk_level: riskData.risk_level || this.determineRiskLevel(riskData.risk_score || 0),
                confidence: riskData.confidence || 0.85,
                profile: riskData.profile || {
                    explanation: riskData.reasoning ? [riskData.reasoning.explanation] : []
                },
                matrix: riskData.profile?.matrix || riskData.matrix || {
                    probability: 'medium',
                    severity: 'medium',
                    quadrant: 5,
                    description: 'Medium risk level'
                },
                factors: riskData.profile?.factors || riskData.factors || {},
                drivers: riskData.drivers || riskData.key_drivers || [],
                recommendations: riskData.recommendations || [],
                timeline: riskData.timeline || [],
                network: riskData.network || riskData.details?.network || {},
                route: route
            };
            
            // Add scenario comparisons if available
            if (window.RISKCAST && window.RISKCAST.modules && window.RISKCAST.modules.ScenarioSimulation) {
                const scenarioSim = window.RISKCAST.modules.ScenarioSimulation;
                if (scenarioSim.currentSimulation) {
                    reportData.scenario_comparisons = [{
                        name: 'Current Scenario',
                        baseline_score: riskData.risk_score || 0,
                        simulation_score: scenarioSim.currentSimulation.simulation_score || 0,
                        delta_from_baseline: scenarioSim.currentSimulation.delta_from_baseline || 0,
                        explanation: {}
                    }];
                }
            }
            
            return reportData;
        },

        /**
         * Determine risk level from score
         */
        determineRiskLevel: function(score) {
            if (score >= 85) return 'Critical';
            if (score >= 70) return 'High';
            if (score >= 50) return 'Medium';
            if (score >= 30) return 'Low-Medium';
            return 'Low';
        },

        /**
         * Set loading state
         */
        setLoadingState: function(loading) {
            const btn = document.getElementById('exportPdfBtn');
            if (!btn) return;
            
            if (loading) {
                btn.disabled = true;
                const span = btn.querySelector('span');
                if (span) {
                    span.textContent = 'Generating...';
                }
                btn.classList.add('loading');
            } else {
                btn.disabled = false;
                const span = btn.querySelector('span');
                if (span) {
                    span.textContent = 'Export PDF';
                }
                btn.classList.remove('loading');
            }
        }
    };
    
    // Export
    window.RISKCAST.modules.PDFExport = PDFExport;
    
    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => PDFExport.init(), 1000);
        });
    } else {
        setTimeout(() => PDFExport.init(), 1000);
    }
})();




















