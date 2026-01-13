
(function() {
    'use strict';

    if (typeof window.RISKCAST === 'undefined') {
        window.RISKCAST = {};
    }
    if (typeof window.RISKCAST.visualization === 'undefined') {
        window.RISKCAST.visualization = {};
    }
    if (typeof window.RISKCAST.visualization.results === 'undefined') {
        window.RISKCAST.visualization.results = {};
    }

    const resultsViz = window.RISKCAST.visualization.results;
    const gauge = window.RISKCAST.visualization.gauge || {};
    const heatmap = window.RISKCAST.visualization.heatmap || {};
    const radar = window.RISKCAST.visualization.radar || {};
    const driversBar = window.RISKCAST.visualization.driversBar || {};
    const timeline = window.RISKCAST.visualization.timeline || {};
    const network = window.RISKCAST.visualization.networkGraph || window.RISKCAST.visualization.network || {};

    // Store chart instances for lifecycle management
    const chartInstances = {
        gauge: null,
        heatmap: null,
        radar: null,
        driversBar: null,
        timeline: null,
        network: null
    };

    /**
     * Fetch risk analysis from Engine v2 API
     * @param {Object} shipmentData - Shipment input data
     * @returns {Promise<Object>} Risk analysis result
     */
    async function fetchRiskAnalysis(shipmentData) {
        try {
            const response = await fetch('/api/v1/risk/v2/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(shipmentData)
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('[Visualization] Failed to fetch risk analysis:', error);
            return null;
        }
    }

    /**
     * Normalize factors from array to object format (for radar/drivers charts)
     * @param {any} factors - Factors in any format
     * @returns {Object} Object with factor keys and values
     */
    function normalizeFactors(factors) {
        if (!factors) return {};
        
        // If already an object, return it
        if (typeof factors === 'object' && !Array.isArray(factors)) {
            return factors;
        }
        
        // If it's an array, convert to object
        if (Array.isArray(factors)) {
            const result = {};
            factors.forEach((factor, index) => {
                if (typeof factor === 'object' && factor !== null) {
                    // If factor has a name/key property
                    const key = factor.name || factor.factor || factor.key || `factor_${index}`;
                    const value = factor.score || factor.value || factor.contribution || 0;
                    result[key] = value;
                } else if (typeof factor === 'string') {
                    // If it's just a string, use it as key with default value
                    result[factor] = 0;
                }
            });
            return result;
        }
        
        return {};
    }

    /**
     * Normalize recommendations to array format
     * @param {any} recommendations - Recommendations in any format
     * @returns {Array} Array of recommendation strings
     */
    function normalizeRecommendations(recommendations) {
        if (!recommendations) return [];
        
        // If already an array, return it
        if (Array.isArray(recommendations)) {
            return recommendations;
        }
        
        // If it's an object, try to extract array from common properties
        if (typeof recommendations === 'object') {
            // Try common property names
            if (recommendations.all_recommendations && Array.isArray(recommendations.all_recommendations)) {
                return recommendations.all_recommendations;
            }
            if (recommendations.priority_actions && Array.isArray(recommendations.priority_actions)) {
                return recommendations.priority_actions;
            }
            if (recommendations.actions && Array.isArray(recommendations.actions)) {
                return recommendations.actions;
            }
            if (recommendations.suggestions && Array.isArray(recommendations.suggestions)) {
                return recommendations.suggestions;
            }
            // If object has string values, convert to array
            const values = Object.values(recommendations).filter(v => typeof v === 'string');
            if (values.length > 0) {
                return values;
            }
        }
        
        // If it's a string, wrap in array
        if (typeof recommendations === 'string') {
            return [recommendations];
        }
        
        return [];
    }

    /**
     * Map backend result to visualization format
     * @param {Object} apiResult - Result from Engine v2 API
     * @returns {Object} Mapped data for visualizations
     */
    function mapDataToVisualizations(apiResult) {
        if (!apiResult) return null;

        return {
            // Overall risk score
            riskScore: apiResult.risk_score || apiResult.overall_risk || 0,
            riskLevel: apiResult.risk_level || 'moderate',
            confidence: apiResult.confidence || 0.5,

            // Risk factors for radar/drivers (keep as-is, will normalize when rendering)
            factors: apiResult.profile?.factors || apiResult.risk_factors || [],

            // Impact matrix for heatmap
            matrix: apiResult.profile?.matrix || apiResult.impact_matrix || null,

            // Timeline data
            timeline: Array.isArray(apiResult.timeline) ? apiResult.timeline : 
                     Array.isArray(apiResult.risk_evolution) ? apiResult.risk_evolution : [],

            // Network data
            network: apiResult.network || apiResult.port_network || null,

            // Recommendations - normalize to array
            recommendations: normalizeRecommendations(apiResult.recommendations)
        };
    }

    /**
     * Initialize empty visualizations (create chart containers without data)
     * Called once on page load before data is available
     */
    function initVisuals() {
        console.log('[Visualization] Initializing empty visualizations...');

        // Initialize gauge with default value (will animate when data arrives)
        if (gauge.create && typeof gauge.create === 'function') {
            chartInstances.gauge = gauge.create('confidence-gauge', 0.5);
            console.log('[Visualization] ✓ Gauge initialized');
        }

        // Initialize heatmap with empty matrix
        if (heatmap.create && typeof heatmap.create === 'function') {
            const defaultMatrix = [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0]
            ];
            chartInstances.heatmap = heatmap.create('risk-heatmap', defaultMatrix);
            console.log('[Visualization] ✓ Heatmap initialized');
        }

        // Initialize radar with default factors
        if (radar.create && typeof radar.create === 'function') {
            const defaultFactors = {
                delay: 0,
                port: 0,
                climate: 0,
                carrier: 0,
                esg: 0,
                equipment: 0
            };
            chartInstances.radar = radar.create('risk-radar', defaultFactors);
            console.log('[Visualization] ✓ Radar initialized');
        }

        // Initialize driver bar with default factors
        if (driversBar.create && typeof driversBar.create === 'function') {
            const defaultFactors = {
                delay: 0,
                port: 0,
                climate: 0,
                carrier: 0,
                esg: 0,
                equipment: 0
            };
            chartInstances.driversBar = driversBar.create('risk-drivers', defaultFactors);
            console.log('[Visualization] ✓ Driver bar initialized');
        }

        // Initialize timeline with empty data
        if (timeline.create && typeof timeline.create === 'function') {
            const defaultTimeline = Array.from({ length: 7 }, (_, i) => ({
                day: i + 1,
                score: 0
            }));
            chartInstances.timeline = timeline.create('risk-timeline', defaultTimeline);
            console.log('[Visualization] ✓ Timeline initialized');
        } else if (timeline.createTimelineChart && typeof timeline.createTimelineChart === 'function') {
            const defaultTimeline = Array.from({ length: 7 }, (_, i) => ({
                day: i + 1,
                score: 0
            }));
            chartInstances.timeline = timeline.createTimelineChart('risk-timeline', defaultTimeline);
            console.log('[Visualization] ✓ Timeline initialized');
        }

        // Initialize network with minimal default
        if (network.create && typeof network.create === 'function') {
            const defaultNetwork = {
                nodes: [
                    { id: 'ORIGIN', risk: 0.5, label: 'Origin' },
                    { id: 'DEST', risk: 0.5, label: 'Destination' }
                ],
                edges: [
                    { from: 'ORIGIN', to: 'DEST', volume: 1, risk: 0.5 }
                ]
            };
            chartInstances.network = network.create('risk-network', defaultNetwork);
            console.log('[Visualization] ✓ Network initialized');
        } else if (network.createNetworkGraph && typeof network.createNetworkGraph === 'function') {
            const defaultNetwork = {
                nodes: [
                    { id: 'ORIGIN', risk: 0.5, label: 'Origin' },
                    { id: 'DEST', risk: 0.5, label: 'Destination' }
                ],
                edges: [
                    { from: 'ORIGIN', to: 'DEST', volume: 1, risk: 0.5 }
                ]
            };
            chartInstances.network = network.createNetworkGraph('risk-network', defaultNetwork);
            console.log('[Visualization] ✓ Network initialized');
        }

        console.log('[Visualization] ✅ All visualizations initialized');
    }

    /**
     * Update visualizations with real data
     * Called after backend data loads
     * 
     * IMPORTANT: This function should ALWAYS run, even if state is frozen.
     * State freezing should only freeze data changes, NOT UI rendering.
     * Visualizations must remain responsive and animated for demo/pitch purposes.
     * 
     * @param {Object} vizData - Mapped visualization data
     */
    function updateVisuals(vizData) {
        if (!vizData) {
            console.warn('[Visualization] No data to update');
            return;
        }
        
        // Always update visuals regardless of state freezing
        // (State freezing should only affect data mutations, not rendering)

        console.log('[Visualization] Updating visualizations with data...', {
            riskScore: vizData.riskScore,
            confidence: vizData.confidence,
            hasFactors: !!vizData.factors,
            hasTimeline: !!vizData.timeline
        });

        // 1. Risk Score Card
        const riskScoreEl = document.getElementById('risk-score-value');
        const riskLevelEl = document.getElementById('risk-level-value');
        if (riskScoreEl) {
            riskScoreEl.textContent = Math.round(vizData.riskScore || 0);
        }
        if (riskLevelEl) {
            riskLevelEl.textContent = (vizData.riskLevel || 'Moderate').toUpperCase();
        }

        // 2. Confidence Gauge - animate to confidence * 100
        const confidence = vizData.confidence != null ? 
            (vizData.confidence > 1 ? vizData.confidence / 100 : vizData.confidence) : 
            0.5;
        
        if (chartInstances.gauge) {
            // Use update method if available
            if (gauge.update && typeof gauge.update === 'function') {
                gauge.update(chartInstances.gauge, confidence);
            } else if (chartInstances.gauge.updateGauge && typeof chartInstances.gauge.updateGauge === 'function') {
                chartInstances.gauge.updateGauge(confidence);
            } else {
                // Recreate if no update method
                chartInstances.gauge = gauge.create('confidence-gauge', confidence);
            }
            console.log('[Visualization] ✓ Gauge updated to', (confidence * 100).toFixed(0) + '%');
        } else if (gauge.create && typeof gauge.create === 'function') {
            chartInstances.gauge = gauge.create('confidence-gauge', confidence);
            console.log('[Visualization] ✓ Gauge created with', (confidence * 100).toFixed(0) + '%');
        }

        // 3. Heatmap (Impact Matrix)
        if (vizData.matrix) {
            if (chartInstances.heatmap && heatmap.update && typeof heatmap.update === 'function') {
                heatmap.update(chartInstances.heatmap, vizData.matrix);
                console.log('[Visualization] ✓ Heatmap updated');
            } else if (heatmap.create && typeof heatmap.create === 'function') {
                chartInstances.heatmap = heatmap.create('risk-heatmap', vizData.matrix);
                console.log('[Visualization] ✓ Heatmap created');
            }
        }

        // 4. Radar Chart (needs object format)
        let factorsObj = normalizeFactors(vizData.factors);
        if (Object.keys(factorsObj).length === 0) {
            // Create default factors from layers if available
            if (Array.isArray(vizData.layers) && vizData.layers.length > 0) {
                factorsObj = {};
                vizData.layers.forEach(layer => {
                    if (layer.name && layer.score != null) {
                        const key = layer.name.toLowerCase().replace(/\s+/g, '_');
                        factorsObj[key] = layer.score / 100; // Normalize to 0-1
                    }
                });
            }
            // If still empty, create default factors
            if (Object.keys(factorsObj).length === 0) {
                factorsObj = {
                    delay: 0,
                    port: 0,
                    climate: 0,
                    carrier: 0,
                    esg: 0,
                    equipment: 0
                };
            }
        }
        
        if (chartInstances.radar && radar.update && typeof radar.update === 'function') {
            radar.update(chartInstances.radar, factorsObj);
            console.log('[Visualization] ✓ Radar updated');
        } else if (radar.create && typeof radar.create === 'function') {
            chartInstances.radar = radar.create('risk-radar', factorsObj);
            console.log('[Visualization] ✓ Radar created');
        }

        // 5. Driver Bar Chart (needs object format)
        if (chartInstances.driversBar && driversBar.update && typeof driversBar.update === 'function') {
            driversBar.update(chartInstances.driversBar, factorsObj);
            console.log('[Visualization] ✓ Driver bar updated');
        } else if (driversBar.create && typeof driversBar.create === 'function') {
            chartInstances.driversBar = driversBar.create('risk-drivers', factorsObj);
            console.log('[Visualization] ✓ Driver bar created');
        }

        // 6. Timeline Chart
        let timelineData = vizData.timeline;
        if (!timelineData || !Array.isArray(timelineData) || timelineData.length === 0) {
            // Generate default timeline from risk score
            const riskScore = vizData.riskScore || 0;
            timelineData = [];
            for (let day = 1; day <= 7; day++) {
                // Simulate slight variation in risk over time
                const variation = (Math.sin(day * 0.5) * 5) + (Math.random() * 3 - 1.5);
                const dayScore = Math.max(0, Math.min(100, riskScore + variation));
                timelineData.push({
                    day: day,
                    score: Math.round(dayScore),
                    risk: dayScore / 100
                });
            }
        }
        
        if (chartInstances.timeline && timeline.update && typeof timeline.update === 'function') {
            timeline.update(chartInstances.timeline, timelineData);
            console.log('[Visualization] ✓ Timeline updated');
        } else if (timeline.create && typeof timeline.create === 'function') {
            chartInstances.timeline = timeline.create('risk-timeline', timelineData);
            console.log('[Visualization] ✓ Timeline created');
        } else if (timeline.createTimelineChart && typeof timeline.createTimelineChart === 'function') {
            chartInstances.timeline = timeline.createTimelineChart('risk-timeline', timelineData);
            console.log('[Visualization] ✓ Timeline created');
        }

        // 7. Network Graph
        let networkData = vizData.network;
        if (!networkData) {
            // Create default network data from layers/route if available
            networkData = {
                nodes: [],
                edges: []
            };
            
            // Try to extract from summary if available
            if (window.__RISKCAST_SUMMARY__) {
                const summary = window.__RISKCAST_SUMMARY__;
                const route = summary.shipment?.routeText || summary.shipment?.route || '';
                if (route) {
                    // Create simple network with origin and destination
                    const parts = route.split('→').map(s => s.trim());
                    if (parts.length >= 2) {
                        networkData.nodes = [
                            { id: parts[0], risk: 0.5, label: parts[0] },
                            { id: parts[1], risk: 0.5, label: parts[1] }
                        ];
                        networkData.edges = [
                            { from: parts[0], to: parts[1], volume: 1, risk: 0.5 }
                        ];
                    }
                }
            }
            
            // If still empty, create minimal default
            if (networkData.nodes.length === 0) {
                networkData.nodes = [
                    { id: 'ORIGIN', risk: 0.5, label: 'Origin' },
                    { id: 'DEST', risk: 0.5, label: 'Destination' }
                ];
                networkData.edges = [
                    { from: 'ORIGIN', to: 'DEST', volume: 1, risk: 0.5 }
                ];
            }
        }
        
        // Network graph needs to be recreated (update method recreates internally)
        if (network.create && typeof network.create === 'function') {
            // Cleanup old instance if exists
            if (chartInstances.network && chartInstances.network.cleanup) {
                chartInstances.network.cleanup();
            }
            chartInstances.network = network.create('risk-network', networkData);
            console.log('[Visualization] ✓ Network updated');
        } else if (network.createNetworkGraph && typeof network.createNetworkGraph === 'function') {
            if (chartInstances.network && chartInstances.network.cleanup) {
                chartInstances.network.cleanup();
            }
            chartInstances.network = network.createNetworkGraph('risk-network', networkData);
            console.log('[Visualization] ✓ Network updated');
        }

        // 8. Recommendations List - generate default if none provided
        const recommendationsList = document.getElementById('risk-recommendations-list');
        if (recommendationsList) {
            // Normalize recommendations to array (defensive programming)
            let recommendations = normalizeRecommendations(vizData.recommendations);
            
            // Generate default recommendations from risk data if none provided
            if (recommendations.length === 0) {
                const riskScore = vizData.riskScore || 0;
                const riskLevel = (vizData.riskLevel || 'moderate').toLowerCase();
                
                recommendations = [];
                if (riskScore > 70 || riskLevel.includes('high')) {
                    recommendations.push('Consider additional insurance coverage for high-risk shipment');
                    recommendations.push('Implement enhanced monitoring and tracking systems');
                    recommendations.push('Review and optimize route selection to minimize exposure');
                    recommendations.push('Coordinate with carrier for priority handling');
                } else if (riskScore > 50 || riskLevel.includes('moderate')) {
                    recommendations.push('Monitor shipment progress regularly');
                    recommendations.push('Ensure proper documentation and compliance');
                    recommendations.push('Maintain communication with all parties');
                } else {
                    recommendations.push('Standard monitoring procedures recommended');
                    recommendations.push('Maintain regular check-ins with carrier');
                }
            }
            
            if (recommendations.length === 0) {
                recommendationsList.innerHTML = '<li>No specific recommendations available</li>';
            } else {
                recommendationsList.innerHTML = recommendations
                    .slice(0, 10) // Limit to 10 recommendations
                    .map(rec => {
                        const text = typeof rec === 'string' ? rec : (rec.text || rec.recommendation || rec.message || '');
                        return text ? `<li>${text}</li>` : '';
                    })
                    .filter(html => html) // Remove empty items
                    .join('');
            }
        }

        console.log('[Visualization] ✅ All visualizations updated with data');
    }

    /**
     * Render all visualizations with data (backward compatibility)
     * @param {Object} vizData - Mapped visualization data
     */
    function renderVisualizations(vizData) {
        // If charts not initialized, initialize first
        if (!chartInstances.gauge && !chartInstances.radar) {
            initVisuals();
        }
        // Then update with data
        updateVisuals(vizData);
    }

    /**
     * Fetch data from multiple API endpoints (GET requests only)
     * @returns {Promise<Object|null>} API result or null
     */
    async function fetchDataFromAPIs() {
        const endpoints = [
            '/results/data',
            '/api/get_last_result'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                if (response.ok) {
                    const data = await response.json();
                    if (data && typeof data === 'object' && !data.error && Object.keys(data).length > 0) {
                        console.log(`[Visualization] Data from ${endpoint}`);
                        return data;
                    }
                }
            } catch (error) {
                console.debug(`[Visualization] Failed ${endpoint}:`, error.message);
                continue;
            }
        }
        
        return null;
    }

    /**
     * Initialize visualizations from shipment data
     * @param {Object} shipmentData - Shipment input data (optional)
     */
    async function initializeVisualizations(shipmentData) {
        // Try to get data from existing sources first
        let vizData = null;

        // 1. Check window.__RISKCAST_SUMMARY__ (from server-side injection)
        if (window.__RISKCAST_SUMMARY__) {
            const summary = window.__RISKCAST_SUMMARY__;
            if (summary && (summary.overall || summary.risk_score || summary.layers)) {
                // Extract factors - try multiple formats
                let factors = [];
                if (Array.isArray(summary.factors)) {
                    factors = summary.factors;
                } else if (Array.isArray(summary.layers)) {
                    factors = summary.layers;
                } else if (summary.factors && typeof summary.factors === 'object') {
                    // If factors is an object, convert to array
                    factors = Object.entries(summary.factors).map(([key, value]) => ({
                        name: key,
                        score: typeof value === 'number' ? value : 0
                    }));
                }
                
                vizData = {
                    riskScore: summary.overall?.riskScore || summary.risk_score || 0,
                    riskLevel: summary.overall?.riskLevel || summary.risk_level || 'moderate',
                    confidence: summary.overall?.confidence || 0.5,
                    factors: factors,
                    layers: summary.layers || [],
                    matrix: summary.matrix || summary.profile?.matrix || null,
                    timeline: Array.isArray(summary.timeline) ? summary.timeline : [],
                    network: summary.network || null,
                    recommendations: normalizeRecommendations(
                        summary.recommendations || summary.narrative?.actions
                    )
                };
            }
        }

        // 2. Check window.__RESULTSOS__ (from main.js)
        if (!vizData && window.__RESULTSOS__) {
            const state = window.__RESULTSOS__.state;
            const summary = window.__RESULTSOS__.summary;
            
            // Try summary first
            if (summary && (summary.overall || summary.layers)) {
                // Extract factors - try multiple formats
                let factors = [];
                if (Array.isArray(summary.factors)) {
                    factors = summary.factors;
                } else if (Array.isArray(summary.layers)) {
                    factors = summary.layers;
                } else if (summary.factors && typeof summary.factors === 'object') {
                    factors = Object.entries(summary.factors).map(([key, value]) => ({
                        name: key,
                        score: typeof value === 'number' ? value : 0
                    }));
                }
                
                vizData = {
                    riskScore: summary.overall?.riskScore || 0,
                    riskLevel: summary.overall?.riskLevel || 'moderate',
                    confidence: summary.overall?.confidence || 0.5,
                    factors: factors,
                    layers: summary.layers || [],
                    matrix: summary.matrix || null,
                    timeline: Array.isArray(summary.timeline) ? summary.timeline : [],
                    network: null,
                    recommendations: normalizeRecommendations(
                        summary.decision?.trace || summary.narrative?.actions
                    )
                };
                console.log('[Visualization] Using window.__RESULTSOS__.summary', {
                    riskScore: vizData.riskScore,
                    factorsCount: factors.length
                });
            }
            // Try state as fallback
            else if (state && (state.globalRisk || state.layers)) {
                // Extract factors - try multiple formats
                let factors = [];
                if (Array.isArray(state.factors)) {
                    factors = state.factors;
                } else if (Array.isArray(state.layers)) {
                    factors = state.layers;
                } else if (state.factors && typeof state.factors === 'object') {
                    factors = Object.entries(state.factors).map(([key, value]) => ({
                        name: key,
                        score: typeof value === 'number' ? value : 0
                    }));
                }
                
                vizData = {
                    riskScore: state.globalRisk || 0,
                    riskLevel: state.decision?.riskLevel || state.profile?.level || 'moderate',
                    confidence: state.decision?.confidence || state.profile?.confidence || 0.5,
                    factors: factors,
                    matrix: null,
                    timeline: [],
                    network: null,
                    recommendations: normalizeRecommendations(state.recommendations?.actions)
                };
                console.log('[Visualization] Using window.__RESULTSOS__.state', {
                    riskScore: vizData.riskScore,
                    factorsCount: factors.length
                });
            }
        }

        // 3. Try to fetch from GET API endpoints (no POST needed)
        if (!vizData) {
            console.log('[Visualization] Fetching data from API endpoints...');
            const apiResult = await fetchDataFromAPIs();
            if (apiResult) {
                vizData = mapDataToVisualizations(apiResult);
            }
        }

        // 4. If still no data and shipmentData provided, try POST API (last resort)
        if (!vizData && shipmentData && shipmentData.route) {
            console.log('[Visualization] Trying POST API as last resort...');
            const apiResult = await fetchRiskAnalysis(shipmentData);
            if (apiResult) {
                vizData = mapDataToVisualizations(apiResult);
            }
        }

        // 5. If still no data, use shipment data directly (fallback with minimal data)
        if (!vizData) {
            if (shipmentData && (shipmentData.risk_score || shipmentData.riskScore)) {
                console.warn('[Visualization] Using fallback data from shipment');
                vizData = {
                    riskScore: shipmentData.risk_score || shipmentData.riskScore || 0,
                    riskLevel: shipmentData.risk_level || shipmentData.riskLevel || 'moderate',
                    confidence: shipmentData.confidence || 0.5,
                    factors: shipmentData.factors || shipmentData.layers || [],
                    matrix: null,
                    timeline: [],
                    network: null,
                    recommendations: []
                };
            } else {
                console.warn('[Visualization] No data available from any source');
                return; // Don't render empty visualizations
            }
        }

        // Initialize visualizations first (empty charts)
        initVisuals();
        
        // Then update with real data (triggers animations)
        updateVisuals(vizData);
    }

    // Expose public API
    resultsViz.fetchRiskAnalysis = fetchRiskAnalysis;
    resultsViz.mapDataToVisualizations = mapDataToVisualizations;
    resultsViz.renderVisualizations = renderVisualizations;
    resultsViz.initializeVisualizations = initializeVisualizations;
    resultsViz.initVisuals = initVisuals;
    resultsViz.updateVisuals = updateVisuals;
    resultsViz.normalizeRecommendations = normalizeRecommendations; // Expose for debugging
    resultsViz.normalizeFactors = normalizeFactors; // Expose for debugging

    console.log('[Visualization] Results v2 integration loaded with lifecycle management');

})();
