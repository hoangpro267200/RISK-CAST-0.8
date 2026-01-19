
(function() {
    'use strict';

    // Initialize module
    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.modules === 'undefined') {
        window.RISKCAST.modules = {};
    }

    const ScenarioSimulation = {
        // State
        baselineResult: null,
        originalInputs: null,
        currentAdjustments: {},
        currentSimulation: null,
        chartInstances: {},
        debounceTimer: null,
        comparisonMode: false,
        
        // Slider IDs mapping
        sliderMap: {
            'slider-port': 'port_congestion',
            'slider-weather': 'weather_hazard',
            'slider-carrier': 'carrier_reliability',
            'slider-esg': 'esg',
            'slider-equipment': 'equipment',
            'slider-network': 'network'
        },
        
        /**
         * Initialize scenario simulation
         */
        init: function() {
            console.log('[Scenario Simulation] Initializing...');
            
            // Wait for baseline result to be available
            this.waitForBaselineResult();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Load saved scenarios
            this.loadSavedScenarios();
            
            // Load presets
            this.loadPresets();
        },
        
        /**
         * Wait for baseline result from ResultsCore
         */
        waitForBaselineResult: function() {
            const checkInterval = setInterval(() => {
                if (window.ResultsCore && window.ResultsCore.data && window.ResultsCore.data.result) {
                    this.baselineResult = window.ResultsCore.data.result;
                    this.originalInputs = window.ResultsCore.data.inputs || {};
                    console.log('[Scenario Simulation] Baseline result loaded');
                    clearInterval(checkInterval);
                    
                    // Initialize baseline display
                    this.updateBaselineDisplay();
                }
            }, 100);
            
            // Timeout after 10 seconds
            setTimeout(() => {
                clearInterval(checkInterval);
                if (!this.baselineResult) {
                    // Only warn if we're actually on a results page
                    if (window.location.pathname.includes('/results')) {
                        console.warn('[Scenario Simulation] Baseline result not found after timeout');
                    }
                }
            }, 10000);
        },
        
        /**
         * Setup event listeners
         */
        setupEventListeners: function() {
            // Slider inputs
            Object.keys(this.sliderMap).forEach(sliderId => {
                const slider = document.getElementById(sliderId);
                if (slider) {
                    slider.addEventListener('input', () => this.onSliderChange(sliderId));
                }
            });
            
            // Preset select
            const presetSelect = document.getElementById('scenario-preset-select');
            if (presetSelect) {
                presetSelect.addEventListener('change', () => this.onPresetSelect());
            }
            
            // Buttons
            const runBtn = document.getElementById('scenario-run-btn');
            if (runBtn) {
                runBtn.addEventListener('click', () => this.runSimulation());
            }
            
            const resetBtn = document.getElementById('scenario-reset-btn');
            if (resetBtn) {
                resetBtn.addEventListener('click', () => this.resetAdjustments());
            }
            
            const saveBtn = document.getElementById('scenario-save-btn');
            if (saveBtn) {
                saveBtn.addEventListener('click', () => this.saveScenario());
            }
            
            const compareToggle = document.getElementById('scenario-compare-toggle');
            if (compareToggle) {
                compareToggle.addEventListener('click', () => this.toggleComparisonMode());
            }
        },
        
        /**
         * Handle slider change (with debounce)
         */
        onSliderChange: function(sliderId) {
            const slider = document.getElementById(sliderId);
            if (!slider) return;
            
            const value = parseFloat(slider.value);
            const factorKey = this.sliderMap[sliderId];
            
            // Update value display
            const valueDisplay = document.getElementById(sliderId + '-value');
            if (valueDisplay) {
                const percentage = Math.round(value * 100);
                valueDisplay.textContent = (percentage >= 0 ? '+' : '') + percentage + '%';
                
                // Color code
                if (percentage > 0) {
                    valueDisplay.style.color = '#ff4444';
                } else if (percentage < 0) {
                    valueDisplay.style.color = '#44ff44';
                } else {
                    valueDisplay.style.color = '#00d4ff';
                }
            }
            
            // Update adjustments
            this.currentAdjustments[factorKey] = value;
            
            // Debounced preview update
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => {
                this.updateSimulationPreview();
            }, 300);
        },
        
        /**
         * Handle preset select
         */
        onPresetSelect: function() {
            const select = document.getElementById('scenario-preset-select');
            if (!select || !select.value) return;
            
            // Fetch preset
            fetch(`/api/v1/risk/v2/simulation/preset/${encodeURIComponent(select.value)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success' && data.preset) {
                        this.applyPreset(data.preset.adjustments);
                    }
                })
                .catch(err => {
                    console.error('[Scenario Simulation] Error loading preset:', err);
                });
        },
        
        /**
         * Apply preset adjustments
         */
        applyPreset: function(adjustments) {
            // Reset all sliders first
            this.resetAdjustments();
            
            // Apply preset adjustments
            Object.keys(adjustments).forEach(factorKey => {
                // Find corresponding slider
                const sliderId = Object.keys(this.sliderMap).find(
                    id => this.sliderMap[id] === factorKey
                );
                
                if (sliderId) {
                    const slider = document.getElementById(sliderId);
                    if (slider) {
                        slider.value = adjustments[factorKey];
                        this.onSliderChange(sliderId);
                    }
                }
            });
            
            // Trigger simulation
            setTimeout(() => this.runSimulation(), 500);
        },
        
        /**
         * Reset all adjustments
         */
        resetAdjustments: function() {
            Object.keys(this.sliderMap).forEach(sliderId => {
                const slider = document.getElementById(sliderId);
                if (slider) {
                    slider.value = 0;
                    this.onSliderChange(sliderId);
                }
            });
            
            this.currentAdjustments = {};
            
            // Clear preset select
            const presetSelect = document.getElementById('scenario-preset-select');
            if (presetSelect) {
                presetSelect.value = '';
            }
        },
        
        /**
         * Update simulation preview (lightweight, no API call)
         */
        updateSimulationPreview: function() {
            // This is a lightweight preview - just show adjustments
            // Full simulation requires API call via runSimulation()
            
            const hasAdjustments = Object.keys(this.currentAdjustments).some(
                key => Math.abs(this.currentAdjustments[key]) > 0.01
            );
            
            if (!hasAdjustments) {
                // Reset to baseline
                this.updateBaselineDisplay();
                return;
            }
            
            // Show preview state (adjustments made but not run)
            const scoreDisplay = document.getElementById('scenario-current-score');
            if (scoreDisplay) {
                scoreDisplay.textContent = '...';
            }
            
            const explanation = document.getElementById('scenario-explanation');
            if (explanation) {
                explanation.textContent = 'Adjustments made. Click "Run Simulation" to see results.';
            }
        },
        
        /**
         * Run full simulation
         */
        runSimulation: async function() {
            if (!this.baselineResult) {
                console.error('[Scenario Simulation] Baseline result not available');
                return;
            }
            
            // Check if there are any adjustments
            const hasAdjustments = Object.keys(this.currentAdjustments).some(
                key => Math.abs(this.currentAdjustments[key]) > 0.01
            );
            
            if (!hasAdjustments) {
                // Reset to baseline
                this.updateBaselineDisplay();
                return;
            }
            
            // Show loading state
            this.setLoadingState(true);
            
            try {
                // Call simulation API
                const response = await fetch('/api/v1/risk/v2/simulate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        baseline_result: this.baselineResult,
                        adjustments: this.currentAdjustments,
                        original_inputs: this.originalInputs
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.status === 'success' && data.simulation) {
                    this.currentSimulation = data.simulation;
                    this.updateSimulationDisplay(data.simulation);
                    
                    // Update comparison if in comparison mode
                    if (this.comparisonMode) {
                        this.updateComparisonDisplay();
                    }
                } else {
                    throw new Error('Invalid response format');
                }
            } catch (error) {
                console.error('[Scenario Simulation] Error running simulation:', error);
                this.showError('Failed to run simulation: ' + error.message);
            } finally {
                this.setLoadingState(false);
            }
        },
        
        /**
         * Update baseline display
         */
        updateBaselineDisplay: function() {
            if (!this.baselineResult) return;
            
            const score = this.baselineResult.risk_score || 0;
            const scoreDisplay = document.getElementById('scenario-current-score');
            if (scoreDisplay) {
                scoreDisplay.textContent = Math.round(score);
            }
            
            // Update baseline comparison if in comparison mode
            if (this.comparisonMode) {
                const baselineScore = document.getElementById('scenario-baseline-score');
                if (baselineScore) {
                    baselineScore.textContent = Math.round(score);
                }
            }
        },
        
        /**
         * Update simulation display
         */
        updateSimulationDisplay: function(simulation) {
            if (!simulation) return;
            
            // Update score
            const score = simulation.simulation_score || 0;
            const scoreDisplay = document.getElementById('scenario-current-score');
            if (scoreDisplay) {
                scoreDisplay.textContent = Math.round(score);
            }
            
            // Update delta
            const delta = simulation.delta_from_baseline || 0;
            const deltaDisplay = document.getElementById('scenario-score-delta');
            if (deltaDisplay) {
                const sign = delta >= 0 ? '+' : '';
                deltaDisplay.textContent = sign + Math.round(delta);
                deltaDisplay.className = 'scenario-score-delta ' + (delta >= 0 ? 'positive' : 'negative');
            }
            
            // Update explanation
            const explanation = document.getElementById('scenario-explanation');
            if (explanation && simulation.profile) {
                explanation.textContent = simulation.profile.explanation || 'Simulation completed';
            }
            
            // Update charts
            this.updateCharts(simulation);
        },
        
        /**
         * Update all charts with simulation data
         */
        updateCharts: function(simulation) {
            // Update radar chart
            if (simulation.factors && window.RISKCAST && window.RISKCAST.visualization) {
                // Use existing radar chart utility
                const radarContainer = document.getElementById('scenario-radar-chart');
                if (radarContainer && window.RISKCAST.visualization.createRadarChart) {
                    window.RISKCAST.visualization.createRadarChart('scenario-radar-chart', simulation.factors);
                }
            }
            
            // Update drivers chart
            if (simulation.drivers_changed) {
                this.updateDriversChart(simulation.drivers_changed);
            }
            
            // Update heatmap
            if (simulation.matrix) {
                this.updateHeatmap(simulation.matrix);
            }
        },
        
        /**
         * Update drivers bar chart
         */
        updateDriversChart: function(drivers) {
            // Implementation would use Chart.js to update bar chart
            // This is a simplified version
            const container = document.getElementById('scenario-drivers-chart');
            if (!container) return;
            
            // Clear and rebuild chart (would integrate with existing drivers_bar.js)
            console.log('[Scenario Simulation] Updating drivers chart:', drivers);
        },
        
        /**
         * Update heatmap
         */
        updateHeatmap: function(matrix) {
            // Implementation would use existing heatmap visualization
            const container = document.getElementById('scenario-heatmap-chart');
            if (!container) return;
            
            console.log('[Scenario Simulation] Updating heatmap:', matrix);
        },
        
        /**
         * Toggle comparison mode
         */
        toggleComparisonMode: function() {
            this.comparisonMode = !this.comparisonMode;
            
            const comparisonView = document.getElementById('scenario-comparison-view');
            const singleView = document.getElementById('scenario-single-view');
            
            if (this.comparisonMode) {
                comparisonView.classList.remove('view-hidden');
                singleView.classList.add('view-hidden');
                this.updateComparisonDisplay();
            } else {
                comparisonView.classList.add('view-hidden');
                singleView.classList.remove('view-hidden');
            }
        },
        
        /**
         * Update comparison display
         */
        updateComparisonDisplay: function() {
            if (!this.baselineResult || !this.currentSimulation) return;
            
            // Calculate delta
            const baselineScore = this.baselineResult.risk_score || 0;
            const simulationScore = this.currentSimulation.simulation_score || 0;
            const delta = simulationScore - baselineScore;
            
            // Update delta display
            const deltaValue = document.getElementById('scenario-delta-value');
            if (deltaValue) {
                const sign = delta >= 0 ? '+' : '';
                deltaValue.textContent = sign + Math.round(delta);
                deltaValue.className = 'scenario-delta-value ' + (delta >= 0 ? 'positive' : 'negative');
            }
            
            // Update baseline and scenario columns
            // (would update charts and drivers lists here)
        },
        
        /**
         * Save scenario
         */
        saveScenario: async function() {
            const nameInput = document.getElementById('scenario-name-input');
            if (!nameInput || !nameInput.value.trim()) {
                alert('Please enter a scenario name');
                return;
            }
            
            const name = nameInput.value.trim();
            
            try {
                const response = await fetch('/api/v1/risk/v2/simulation/save', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: name,
                        adjustments: this.currentAdjustments,
                        result: this.currentSimulation,
                        baseline_score: this.baselineResult ? this.baselineResult.risk_score : null,
                        description: `Saved scenario: ${name}`
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Clear input
                    nameInput.value = '';
                    
                    // Reload saved scenarios
                    this.loadSavedScenarios();
                    
                    alert('Scenario saved successfully!');
                } else {
                    throw new Error(data.detail || 'Failed to save scenario');
                }
            } catch (error) {
                console.error('[Scenario Simulation] Error saving scenario:', error);
                alert('Failed to save scenario: ' + error.message);
            }
        },
        
        /**
         * Load saved scenarios
         */
        loadSavedScenarios: async function() {
            try {
                // Endpoint not implemented yet - skip silently
                // const response = await fetch('/api/v1/risk/v2/simulation/list');
                // const data = await response.json();
                // 
                // if (data.status === 'success') {
                //     this.renderSavedScenarios(data.scenarios || []);
                // }
            } catch (error) {
                // Silently handle - endpoint not available
                // console.error('[Scenario Simulation] Error loading scenarios:', error);
            }
        },
        
        /**
         * Render saved scenarios list
         */
        renderSavedScenarios: function(scenarios) {
            const container = document.getElementById('scenario-saved-list');
            if (!container) return;
            
            if (scenarios.length === 0) {
                container.innerHTML = '<p class="scenario-empty-text">No saved scenarios</p>';
                return;
            }
            
            container.innerHTML = scenarios.map(scenario => `
                <div class="scenario-saved-item" data-scenario-name="${scenario.name}">
                    <span class="scenario-saved-item-name">${scenario.name}</span>
                    <button class="scenario-saved-item-delete" onclick="RISKCAST.modules.ScenarioSimulation.deleteScenario('${scenario.name}')">×</button>
                </div>
            `).join('');
            
            // Add click handlers
            container.querySelectorAll('.scenario-saved-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('scenario-saved-item-delete')) {
                        const name = item.dataset.scenarioName;
                        this.loadScenario(name);
                    }
                });
            });
        },
        
        /**
         * Load scenario
         */
        loadScenario: async function(name) {
            try {
                const response = await fetch(`/api/v1/risk/v2/simulation/load/${encodeURIComponent(name)}`);
                const data = await response.json();
                
                if (data.status === 'success' && data.scenario) {
                    this.applyPreset(data.scenario.adjustments || {});
                }
            } catch (error) {
                console.error('[Scenario Simulation] Error loading scenario:', error);
                alert('Failed to load scenario: ' + error.message);
            }
        },
        
        /**
         * Delete scenario
         */
        deleteScenario: async function(name) {
            if (!confirm(`Delete scenario "${name}"?`)) return;
            
            try {
                const response = await fetch(`/api/v1/risk/v2/simulation/delete/${encodeURIComponent(name)}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.loadSavedScenarios();
                }
            } catch (error) {
                console.error('[Scenario Simulation] Error deleting scenario:', error);
                alert('Failed to delete scenario: ' + error.message);
            }
        },
        
        /**
         * Load presets
         */
        loadPresets: async function() {
            // Presets are hardcoded in HTML select, but we could load dynamically here
            // For now, just ensure select is populated
        },
        
        /**
         * Set loading state
         */
        setLoadingState: function(loading) {
            const container = document.getElementById('scenario-simulation-card');
            if (container) {
                if (loading) {
                    container.classList.add('scenario-loading');
                } else {
                    container.classList.remove('scenario-loading');
                }
            }
            
            const runBtn = document.getElementById('scenario-run-btn');
            if (runBtn) {
                runBtn.disabled = loading;
                runBtn.textContent = loading ? 'Running...' : 'Run Simulation';
            }
        },
        
        /**
         * Show error
         */
        showError: function(message) {
            const explanation = document.getElementById('scenario-explanation');
            if (explanation) {
                explanation.innerHTML = `<span style="color: #ff4444;">Error: ${message}</span>`;
            }
        }
    };
    
    // Export
    window.RISKCAST.modules.ScenarioSimulation = ScenarioSimulation;
    
    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => ScenarioSimulation.init(), 1000);
        });
    } else {
        setTimeout(() => ScenarioSimulation.init(), 1000);
    }
})();









