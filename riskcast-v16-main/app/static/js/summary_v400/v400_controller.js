/* ==========================================================================
   SUMMARY_V400 - CONTROLLER
   Main orchestrator - initializes and coordinates all modules
   ========================================================================== */

const V400Controller = (() => {
    let currentState = null;
    let validationResults = null;
    
    /**
     * Initialize application
     */
    function init() {
        console.log('🚀 Initializing SUMMARY_V400...');
        
        // Load state
        currentState = V400State.loadState();
        console.log('✓ State loaded:', currentState);
        
        // Initialize editor
        V400InlineEditor.init(handleStateSave);
        
        // Initial render
        refresh();
        
        // Attach event handlers
        attachEventHandlers();
        
        // Show action strip after a moment
        setTimeout(() => {
            const actionStrip = document.getElementById('actionStrip');
            if (actionStrip) {
                actionStrip.classList.add('action-strip--visible');
            }
        }, 500);
        
        console.log('✓ SUMMARY_V400 ready');
    }
    
    /**
     * Refresh all UI components
     */
    function refresh() {
        // Run validation
        validationResults = V400Validator.evaluateAll(currentState);
        
        // Render components
        V400Renderer.renderBanner(currentState, validationResults);
        V400Renderer.renderAllPanels(currentState, validationResults);
        V400AIAdvisor.render(validationResults, handleAdvisorItemClick);
        V400AIAdvisor.attachHandlers(handleAdvisorItemClick);
        V400RiskRow.render(currentState, handleRiskToggle);
        
        // Update completeness
        updateCompleteness();
        
        // Update error chips
        updateErrorChips();
        
        // Re-attach field click handlers
        attachFieldClickHandlers();
    }
    
    /**
     * Handle state save from editor
     */
    function handleStateSave(newState) {
        currentState = newState;
        V400State.saveState(currentState);
        refresh();
    }
    
    /**
     * Handle risk module toggle
     */
    function handleRiskToggle(moduleKey, isOn) {
        currentState.riskModules[moduleKey] = isOn;
        V400State.saveState(currentState);
        
        // Re-run validation as some rules depend on risk modules
        refresh();
    }
    
    /**
     * Handle advisor item click
     */
    function handleAdvisorItemClick(ruleId, fieldPaths) {
        // Highlight affected fields
        V400AIAdvisor.highlightFields(fieldPaths);
        
        // Open editor for first field
        if (fieldPaths.length > 0) {
            const firstPath = fieldPaths[0];
            const fieldKey = findFieldKeyByPath(firstPath);
            
            if (fieldKey) {
                const tile = document.querySelector(`.field-tile[data-field="${fieldKey}"]`);
                if (tile) {
                    setTimeout(() => {
                        V400InlineEditor.open(fieldKey, tile, currentState);
                    }, 300);
                }
            }
        }
    }
    
    /**
     * Find field key by path
     */
    function findFieldKeyByPath(path) {
        for (const [key, config] of Object.entries(V400Renderer.FIELD_MAP)) {
            if (config.path === path) {
                return key;
            }
        }
        return null;
    }
    
    /**
     * Attach event handlers
     */
    function attachEventHandlers() {
        // Back button
        const btnBack = document.getElementById('btnBack');
        if (btnBack) {
            btnBack.addEventListener('click', () => {
                if (confirm('Go back? Unsaved changes will be lost.')) {
                    window.history.back();
                }
            });
        }
        
        // Save draft buttons
        const saveDraftBtns = [
            document.getElementById('btnSaveDraft'),
            document.getElementById('btnSaveDraftBottom')
        ];
        
        saveDraftBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', () => {
                    V400State.saveState(currentState);
                    showToast('Draft saved successfully!', 'success');
                });
            }
        });
        
        // Confirm buttons
        const confirmBtns = [
            document.getElementById('btnConfirm'),
            document.getElementById('btnConfirmBottom')
        ];
        
        confirmBtns.forEach(btn => {
            if (btn) {
                btn.addEventListener('click', handleConfirm);
            }
        });
    }
    
    /**
     * Attach field click handlers
     */
    function attachFieldClickHandlers() {
        // Field tiles in panels
        const fieldTiles = document.querySelectorAll('.field-tile');
        fieldTiles.forEach(tile => {
            tile.addEventListener('click', (e) => {
                e.stopPropagation();
                const fieldKey = tile.dataset.field;
                V400InlineEditor.open(fieldKey, tile, currentState);
            });
        });
        
        // Banner tiles
        const bannerTiles = document.querySelectorAll('.banner-tile');
        bannerTiles.forEach(tile => {
            tile.addEventListener('click', (e) => {
                e.stopPropagation();
                const fieldKey = tile.dataset.field;
                V400InlineEditor.open(fieldKey, tile, currentState);
            });
        });
        
        // Mega tiles
        const megaTiles = document.querySelectorAll('.mega-tile');
        megaTiles.forEach(tile => {
            tile.addEventListener('click', (e) => {
                e.stopPropagation();
                const fieldKey = tile.dataset.field;
                V400InlineEditor.open(fieldKey, tile, currentState);
            });
        });
    }
    
    /**
     * Update completeness bar
     */
    function updateCompleteness() {
        const percentage = V400State.calculateCompleteness(currentState);
        
        const bar = document.getElementById('completenessBar');
        const value = document.getElementById('completenessValue');
        
        if (bar) {
            bar.style.width = `${percentage}%`;
        }
        
        if (value) {
            value.textContent = `${percentage}%`;
        }
    }
    
    /**
     * Update error chips
     */
    function updateErrorChips() {
        const criticalChip = document.getElementById('chipCritical');
        const warningChip = document.getElementById('chipWarning');
        
        if (criticalChip) {
            const count = validationResults.critical.length;
            const countEl = criticalChip.querySelector('.error-chip__count');
            if (countEl) {
                countEl.textContent = count;
            }
            criticalChip.style.display = count > 0 ? 'flex' : 'none';
        }
        
        if (warningChip) {
            const count = validationResults.warning.length;
            const countEl = warningChip.querySelector('.error-chip__count');
            if (countEl) {
                countEl.textContent = count;
            }
            warningChip.style.display = count > 0 ? 'flex' : 'none';
        }
    }
    
    /**
     * Direct export summary state (fallback if module not loaded)
     * @param {Object} summaryData - Summary data
     */
    function exportSummaryStateDirect(summaryData) {
        const SUMMARY_STATE_KEY = 'RISKCAST_SUMMARY_STATE';
        const timestamp = new Date().toISOString();
        const shipment = summaryData.shipment || {};
        const route = shipment.route || '';
        
        const summaryState = {
            version: '1.0.0',
            timestamp: timestamp,
            shipmentId: shipment.id || `SH-${Date.now()}`,
            shipment: {
                id: shipment.id || `SH-${Date.now()}`,
                route: route,
                transportMode: shipment.transportMode || '',
                cargoType: shipment.cargoType || '',
                container: shipment.container || '',
                incoterm: shipment.incoterm || '',
                cargoValue: shipment.cargoValue || 0,
                etd: shipment.etd || '',
                eta: shipment.eta || '',
                transitTime: shipment.transitTime || 0,
                distance: shipment.distance || 0,
                origin: shipment.origin || '',
                destination: shipment.destination || '',
                carrier: shipment.carrier || '',
                packaging: shipment.packaging || '',
                weight: shipment.weight || null,
                volume: shipment.volume || null
            },
            riskModules: summaryData.riskModules || {
                esg: false,
                weather: false,
                congestion: false,
                carrier_perf: false,
                market: false,
                insurance: false
            },
            riskInputs: summaryData.riskInputs || {
                portCongestion: null,
                weatherVolatility: null,
                carrierReliability: null,
                geopolitical: null,
                financial: null,
                esg: null
            },
            source: 'summary_page',
            validated: false
        };
        
        try {
            const serialized = JSON.stringify(summaryState);
            if (typeof sessionStorage !== 'undefined') {
                sessionStorage.setItem(SUMMARY_STATE_KEY, serialized);
            }
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem(SUMMARY_STATE_KEY, serialized);
            }
        } catch (error) {
            console.error('Failed to persist summary state:', error);
        }
    }
    
    /**
     * Transform v400 state to summary export format
     * @param {Object} state - V400 state
     * @param {Object} analysisResult - Analysis result from API (optional)
     * @returns {Object} Summary data for export
     */
    function transformStateForExport(state, analysisResult) {
        const route = state.shipment?.trade_route || {};
        const cargo = state.shipment?.cargo_packing || {};
        
        // Extract risk inputs from analysis result if available
        const riskInputs = analysisResult ? {
            portCongestion: analysisResult.details?.components?.network_risk ? Math.round(analysisResult.details.components.network_risk * 100) : null,
            weatherVolatility: analysisResult.details?.components?.climate_risk ? Math.round(analysisResult.details.components.climate_risk * 100) : null,
            carrierReliability: analysisResult.details?.components?.operational_risk ? Math.round(analysisResult.details.components.operational_risk * 100) : null,
            geopolitical: null, // Not in current analysis
            financial: null, // Not in current analysis
            esg: analysisResult.details?.components?.esg_risk ? Math.round(analysisResult.details.components.esg_risk * 100) : null
        } : {
            portCongestion: null,
            weatherVolatility: null,
            carrierReliability: null,
            geopolitical: null,
            financial: null,
            esg: null
        };
        
        return {
            shipment: {
                id: analysisResult?.shipment_id || `SH-${Date.now()}`,
                route: route.pol && route.pod ? `${route.pol} → ${route.pod}` : (route.pol || route.pod || ''),
                transportMode: route.mode || '',
                cargoType: cargo.cargo_type || '',
                container: route.container_type || '',
                incoterm: route.incoterm || '',
                cargoValue: cargo.cargo_value || 0,
                etd: route.etd || '',
                eta: route.eta || '',
                transitTime: route.transit_time_days || 0,
                distance: 0,
                origin: route.pol || '',
                destination: route.pod || '',
                carrier: route.carrier || '',
                packaging: cargo.packing_type || '',
                weight: cargo.gross_weight_kg || null,
                volume: cargo.volume_cbm || null
            },
            riskModules: state.riskModules || {
                esg: false,
                weather: false,
                congestion: false,
                carrier_perf: false,
                market: false,
                insurance: false
            },
            riskInputs: riskInputs
        };
    }
    
    /**
     * Transform v400 state to API shipment format
     * CRITICAL: Include all required fields for engine
     */
    function buildShipmentPayload(state) {
        const route = state.shipment.trade_route;
        const cargo = state.shipment.cargo_packing;
        
        // Build route string (format: "POL_POD" for backend compatibility)
        const routeStr = route.pol && route.pod 
            ? `${route.pol}_${route.pod}`
            : route.pol || route.pod || '';
        
        // Extract cargo value from cargo_packing or use 0 as fallback
        const cargoValue = cargo.cargo_value || cargo.value || 0;
        
        return {
            transport_mode: route.mode || 'ocean_fcl',
            cargo_type: cargo.cargo_type || 'general',
            route: routeStr,
            pol_code: route.pol || '',
            pod_code: route.pod || '',
            incoterm: route.incoterm || 'FOB',
            carrier: route.carrier || '',
            container: route.container_type || '40HC',
            packaging: cargo.packing_type || 'palletized',
            priority: route.priority || 'standard',
            packages: cargo.packages || 1,
            etd: route.etd || '',
            eta: route.eta || '',
            transit_time: route.transit_time_days || 0,
            cargo_value: cargoValue,
            shipment_value: cargoValue,
            distance: 0,
            use_fuzzy: true,
            use_forecast: true,
            use_mc: true,
            use_var: true,
            // Optional fields
            cargo_weight: cargo.gross_weight_kg || null,
            cargo_volume: cargo.volume_cbm || null,
            hs_code: cargo.hs_code || '',
            buyer: state.shipment.buyer || {},
            seller: state.shipment.seller || {}
        };
    }
    
    /**
     * Handle confirm action - Run Engine v2 analysis and save to localStorage
     */
    async function handleConfirm() {
        // Check for critical errors
        if (validationResults.critical.length > 0) {
            showToast('Please fix all critical errors before confirming', 'error');
            return;
        }
        
        // Check completeness
        const completeness = V400State.calculateCompleteness(currentState);
        if (completeness < 70) {
            const proceed = confirm(
                `Shipment is only ${completeness}% complete. Continue anyway?`
            );
            if (!proceed) return;
        }
        
        // Save state
        V400State.saveState(currentState);
        
        // Show loading
        showToast('Running risk analysis...', 'info');
        
        try {
            // Build API payload
            const shipmentPayload = buildShipmentPayload(currentState);
            
            // Call Engine v2 risk analysis API
            const response = await fetch('/api/v1/risk/v2/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(shipmentPayload)
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const apiResponse = await response.json();
            
            // Extract result from API response
            const engineResult = apiResponse.result || {};
            const route = currentState.shipment.trade_route;
            const cargo = currentState.shipment.cargo_packing;
            
            // Build full analysis object matching required structure
            const fullAnalysis = {
                shipment_id: `SH-${Date.now()}`,
                route: route.pol && route.pod ? `${route.pol} → ${route.pod}` : (route.pol || route.pod || ''),
                pol: route.pol || '',
                pod: route.pod || '',
                carrier: route.carrier || '',
                etd: route.etd || '',
                eta: route.eta || '',
                profile: {
                    score: engineResult.risk_score || 0,
                    level: engineResult.risk_level || 'Medium',
                    confidence: engineResult.confidence || 0,
                    matrix: engineResult.profile?.matrix || {
                        probability: 0,
                        severity: 0,
                        quadrant: '',
                        description: ''
                    },
                    factors: engineResult.profile?.factors || []
                },
                details: {
                    components: engineResult.components || {
                        fahp_weighted: 0,
                        climate_risk: 0,
                        network_risk: 0,
                        operational_risk: 0,
                        missing_data_penalty: 0
                    },
                    climate: engineResult.details?.climate || {
                        storm_probability: 0,
                        wind_index: 0,
                        rainfall_intensity: 0
                    },
                    network: engineResult.details?.network || {
                        port_centrality: 0,
                        carrier_redundancy: 0,
                        propagation_factor: 0
                    },
                    fahp_weights: engineResult.details?.fahp_weights || {},
                    topsis_score: engineResult.details?.topsis_score || 0
                },
                region: engineResult.region || {
                    code: '',
                    name: '',
                    config: {
                        climate_weight: 0,
                        congestion_weight: 0,
                        strike_weight: 0,
                        esg_weight: 0
                    }
                },
                recommendations: engineResult.recommendations || [],
                key_drivers: engineResult.drivers || []
            };
            
            // Remove old localStorage keys
            const oldKeys = [
                'RISKCAST_RESULTS',
                'RISKCAST_RESULTS_V38',
                'RISKCAST_RESULTS_V1',
                'RISKCAST_EVALUATE',
                'evaluate_results',
                'RISKCAST_EVALUATE_V1'
            ];
            oldKeys.forEach(key => {
                localStorage.removeItem(key);
            });
            
            // Save full Engine v2 analysis to localStorage
            localStorage.setItem('RISKCAST_RESULTS_V2', JSON.stringify(fullAnalysis));
            
            console.log('✓ Engine v2 analysis saved to RISKCAST_RESULTS_V2');
            console.log('✓ Old keys removed from localStorage');
            
            // Export summary state for ResultsOS
            const summaryData = transformStateForExport(currentState, fullAnalysis);
            if (typeof window.exportSummaryState === 'function') {
                window.exportSummaryState(summaryData);
                console.log('✓ Summary state exported for ResultsOS');
            } else {
                // Fallback: direct export logic
                exportSummaryStateDirect(summaryData);
                console.log('✓ Summary state exported (direct method)');
            }
            
            // Show success
            showToast('Analysis complete! Redirecting to results...', 'success');
            
            // Redirect to Results page
            setTimeout(() => {
                console.log('→ Redirecting to Results page...');
                window.location.href = '/results';
            }, 1000);
            
        } catch (error) {
            console.error('❌ Risk analysis failed:', error);
            
            // Export summary state even on error (for empty state fallback)
            try {
                const summaryData = transformStateForExport(currentState, null);
                if (typeof window.exportSummaryState === 'function') {
                    window.exportSummaryState(summaryData);
                } else {
                    exportSummaryStateDirect(summaryData);
                }
            } catch (exportError) {
                console.warn('Failed to export summary state:', exportError);
            }
            
            showToast('Analysis failed. Redirecting anyway...', 'warning');
            
            // Redirect anyway (Results page will show empty state)
            setTimeout(() => {
                console.log('→ Redirecting to Results page (with empty state)...');
                window.location.href = '/results';
            }, 1500);
        }
    }
    
    /**
     * Show toast notification
     */
    function showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        toast.textContent = message;
        
        // Style
        Object.assign(toast.style, {
            position: 'fixed',
            bottom: '100px',
            right: '24px',
            padding: '16px 24px',
            background: type === 'success' ? 'var(--accent-green)' : 
                       type === 'error' ? 'var(--accent-red)' : 
                       'var(--accent-cyan)',
            color: type === 'error' ? 'white' : '#000',
            borderRadius: 'var(--radius-pill)',
            fontSize: '14px',
            fontWeight: '600',
            boxShadow: 'var(--shadow-depth-2)',
            zIndex: '10000',
            animation: 'slideInRight 300ms ease-out'
        });
        
        document.body.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.style.animation = 'fadeOut 300ms ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Public API
    return {
        init
    };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', V400Controller.init);
} else {
    V400Controller.init();
}

