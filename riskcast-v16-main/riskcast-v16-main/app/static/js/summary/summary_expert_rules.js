/**
 * =====================================================
 * SUMMARY_EXPERT_RULES.JS – Expert Validation Rules Engine
 * RISKCAST FutureOS v100
 * =====================================================
 * 
 * Industry-standard validation rules for logistics operations
 * Implements smart detection and recommendations
 */

const ExpertRules = (function() {
    'use strict';

    /**
     * RULE 1: ETD Sunday Check
     * Air cargo rarely departs on Sundays
     */
    function checkSundayDeparture(state) {
        const warnings = [];
        
        if (state.trade_route.etd && state.trade_route.mode_of_transport === 'Air') {
            const etdDate = new Date(state.trade_route.etd);
            
            if (etdDate.getDay() === 0) { // Sunday
                const prevFriday = new Date(etdDate);
                prevFriday.setDate(etdDate.getDate() - 2);
                
                const nextMonday = new Date(etdDate);
                nextMonday.setDate(etdDate.getDate() + 1);
                
                warnings.push({
                    type: 'warning',
                    category: 'ETD Schedule',
                    title: 'Sunday Departure Unlikely',
                    message: `Air cargo rarely departs on Sunday (${formatDate(etdDate)}). Consider ${formatDate(prevFriday)} or ${formatDate(nextMonday)}.`,
                    field: 'trade_route.etd',
                    severity: 'medium',
                    icon: '📅'
                });
            }
        }
        
        return warnings;
    }

    /**
     * RULE 2: HS Code Logic
     * Validate HS code implications
     */
    function checkHSCodeLogic(state) {
        const suggestions = [];
        const warnings = [];
        
        const hsCode = state.cargo_packing.hs_code;
        
        if (!hsCode) return [];
        
        // Electronics detection (85xxxx)
        if (hsCode.startsWith('85')) {
            if (state.cargo_packing.stackability !== 'No') {
                suggestions.push({
                    type: 'suggestion',
                    category: 'HS Code Logic',
                    title: 'Electronics - Non-Stackable',
                    message: 'HS 85xxxx (electronics) are typically non-stackable. Consider updating stackability to "No".',
                    field: 'cargo_packing.stackability',
                    severity: 'low',
                    icon: '💡',
                    suggestedValue: 'No'
                });
            }
            
            if (!state.cargo_packing.cargo_sensitivity) {
                suggestions.push({
                    type: 'suggestion',
                    category: 'HS Code Logic',
                    title: 'Electronics - Fragile',
                    message: 'Electronics typically require "Fragile" or "High Value" sensitivity.',
                    field: 'cargo_packing.cargo_sensitivity',
                    severity: 'low',
                    icon: '💡',
                    suggestedValue: 'Fragile'
                });
            }
        }
        
        // Dangerous Goods detection (specific HS codes)
        const dgHSCodes = ['280410', '280700', '290124', '291570'];
        if (dgHSCodes.some(code => hsCode.includes(code))) {
            if (state.cargo_packing.dangerous_goods !== 'Yes') {
                warnings.push({
                    type: 'warning',
                    category: 'Dangerous Goods',
                    title: 'Potential DG Detected',
                    message: 'This HS code may indicate dangerous goods. Please verify and update DG status.',
                    field: 'cargo_packing.dangerous_goods',
                    severity: 'high',
                    icon: '⚠️',
                    suggestedValue: 'Yes'
                });
            }
        }
        
        return [...warnings, ...suggestions];
    }

    /**
     * RULE 3: Weight/CBM Mismatch
     * Validate realistic weight-to-volume ratios
     */
    function checkWeightVolumeRatio(state) {
        const warnings = [];
        
        const grossWeight = parseFloat(state.cargo_packing.gross_weight);
        const volumeCBM = parseFloat(state.cargo_packing.volume_cbm);
        
        if (!grossWeight || !volumeCBM) return [];
        
        const density = grossWeight / volumeCBM; // kg/m³
        
        // Unrealistic high density (>1000 kg/m³ is very dense, like metal)
        if (density > 1000) {
            warnings.push({
                type: 'warning',
                category: 'Weight/Volume',
                title: 'Very High Density Detected',
                message: `Density: ${density.toFixed(0)} kg/m³. This is extremely dense. Please verify weight and volume.`,
                field: 'cargo_packing.gross_weight',
                severity: 'medium',
                icon: '⚖️'
            });
        }
        
        // Unrealistic low density (<10 kg/m³ is very light, like foam)
        if (density < 10) {
            warnings.push({
                type: 'warning',
                category: 'Weight/Volume',
                title: 'Very Low Density Detected',
                message: `Density: ${density.toFixed(1)} kg/m³. This is extremely light. Please verify weight and volume.`,
                field: 'cargo_packing.gross_weight',
                severity: 'medium',
                icon: '⚖️'
            });
        }
        
        // Air freight dimensional weight check
        if (state.trade_route.mode_of_transport === 'Air') {
            const dimWeight = volumeCBM * 167; // Standard air freight factor
            
            if (dimWeight > grossWeight * 1.2) {
                suggestions.push({
                    type: 'suggestion',
                    category: 'Air Freight',
                    title: 'Dimensional Weight Higher',
                    message: `Dimensional weight (${dimWeight.toFixed(0)} kg) exceeds actual weight. Freight will be charged on dim weight.`,
                    field: 'cargo_packing.volume_cbm',
                    severity: 'low',
                    icon: '✈️'
                });
            }
        }
        
        return warnings;
    }

    /**
     * RULE 4: Container Logic
     * Validate container selection vs cargo volume
     */
    function checkContainerLogic(state) {
        const warnings = [];
        
        const volumeCBM = parseFloat(state.cargo_packing.volume_cbm);
        const containerType = state.trade_route.container_type;
        
        if (!volumeCBM || !containerType) return [];
        
        const containerCapacities = {
            '20ft': 33,
            '40ft': 67,
            '40ft HC': 76,
            '45ft HC': 86
        };
        
        const capacity = containerCapacities[containerType];
        
        if (!capacity) return [];
        
        // Volume exceeds container capacity
        if (volumeCBM > capacity) {
            warnings.push({
                type: 'warning',
                category: 'Container',
                title: 'Volume Exceeds Container',
                message: `${volumeCBM} CBM exceeds ${containerType} capacity (${capacity} CBM). Consider larger container or LCL.`,
                field: 'trade_route.container_type',
                severity: 'high',
                icon: '📦'
            });
        }
        
        // Significant underutilization (< 60%)
        const utilization = (volumeCBM / capacity) * 100;
        if (utilization < 60 && state.trade_route.shipment_type === 'FCL') {
            warnings.push({
                type: 'suggestion',
                category: 'Container',
                title: 'Low Container Utilization',
                message: `Only ${utilization.toFixed(0)}% utilized. Consider smaller container or LCL for cost savings.`,
                field: 'trade_route.container_type',
                severity: 'low',
                icon: '💡'
            });
        }
        
        return warnings;
    }

    /**
     * RULE 5: Dangerous Goods Auto-Detection
     * Detect DG keywords in cargo description
     */
    function checkDangerousGoodsKeywords(state) {
        const warnings = [];
        
        const description = (state.cargo_packing.cargo_description || '').toLowerCase();
        const dgKeywords = [
            'battery', 'batteries', 'lithium',
            'chemical', 'acid', 'alkaline',
            'flammable', 'inflammable', 'combustible',
            'explosive', 'radioactive',
            'toxic', 'poison', 'corrosive',
            'compressed gas', 'aerosol'
        ];
        
        const detectedKeywords = dgKeywords.filter(keyword => description.includes(keyword));
        
        if (detectedKeywords.length > 0 && state.cargo_packing.dangerous_goods !== 'Yes') {
            warnings.push({
                type: 'warning',
                category: 'Dangerous Goods',
                title: 'Potential DG Keywords Detected',
                message: `Description contains: "${detectedKeywords.join(', ')}". Please confirm if cargo is DG and update accordingly.`,
                field: 'cargo_packing.dangerous_goods',
                severity: 'high',
                icon: '⚠️',
                suggestedValue: 'Yes'
            });
        }
        
        return warnings;
    }

    /**
     * RULE 6: Incoterm Logic
     * Validate Incoterm appropriateness
     */
    function checkIncotermLogic(state) {
        const suggestions = [];
        
        const incoterm = state.trade_route.incoterm;
        const mode = state.trade_route.mode_of_transport;
        
        if (!incoterm || !mode) return [];
        
        // Sea-only Incoterms
        const seaOnlyIncoterms = ['FAS', 'FOB', 'CFR', 'CIF'];
        if (seaOnlyIncoterms.includes(incoterm) && mode !== 'Sea') {
            suggestions.push({
                type: 'warning',
                category: 'Incoterm',
                title: 'Incoterm Mismatch',
                message: `${incoterm} is sea-only, but mode is ${mode}. Consider FCA, CPT, CIP, DAP, or DDP.`,
                field: 'trade_route.incoterm',
                severity: 'medium',
                icon: '📋'
            });
        }
        
        // EXW distance warning
        if (incoterm === 'EXW') {
            suggestions.push({
                type: 'suggestion',
                category: 'Incoterm',
                title: 'EXW Considerations',
                message: 'EXW places maximum responsibility on buyer. Ensure buyer can handle export customs clearance.',
                field: 'trade_route.incoterm',
                severity: 'low',
                icon: '💡'
            });
        }
        
        return suggestions;
    }

    /**
     * RULE 7: Transit Time Validation
     */
    function checkTransitTime(state) {
        const warnings = [];
        
        const transitTime = parseInt(state.trade_route.transit_time);
        const mode = state.trade_route.mode_of_transport;
        
        if (!transitTime || !mode) return [];
        
        // Unrealistic transit times
        const expectedRanges = {
            'Air': { min: 1, max: 7 },
            'Sea': { min: 7, max: 60 },
            'Road': { min: 1, max: 14 },
            'Rail': { min: 10, max: 30 }
        };
        
        const range = expectedRanges[mode];
        
        if (range) {
            if (transitTime < range.min) {
                warnings.push({
                    type: 'warning',
                    category: 'Transit Time',
                    title: 'Unusually Short Transit',
                    message: `${transitTime} days seems short for ${mode}. Typical range: ${range.min}-${range.max} days.`,
                    field: 'trade_route.transit_time',
                    severity: 'medium',
                    icon: '⏱️'
                });
            }
            
            if (transitTime > range.max) {
                warnings.push({
                    type: 'warning',
                    category: 'Transit Time',
                    title: 'Unusually Long Transit',
                    message: `${transitTime} days seems long for ${mode}. Typical range: ${range.min}-${range.max} days.`,
                    field: 'trade_route.transit_time',
                    severity: 'medium',
                    icon: '⏱️'
                });
            }
        }
        
        return warnings;
    }

    /**
     * RULE 8: Insurance Value Check
     */
    function checkInsuranceValue(state) {
        const suggestions = [];
        
        const insuranceValue = parseFloat(state.cargo_packing.insurance_value_usd);
        const grossWeight = parseFloat(state.cargo_packing.gross_weight);
        
        if (!insuranceValue || !grossWeight) return [];
        
        // Very high value per kg (>$1000/kg)
        const valuePerKg = insuranceValue / grossWeight;
        
        if (valuePerKg > 1000) {
            suggestions.push({
                type: 'suggestion',
                category: 'Insurance',
                title: 'High Value Cargo',
                message: `Value: $${valuePerKg.toFixed(0)}/kg. Consider comprehensive insurance and special handling.`,
                field: 'cargo_packing.insurance_coverage_type',
                severity: 'medium',
                icon: '💰'
            });
        }
        
        // Low insurance coverage for high value
        if (insuranceValue > 50000 && !state.cargo_packing.insurance_coverage_type) {
            suggestions.push({
                type: 'suggestion',
                category: 'Insurance',
                title: 'Insurance Coverage Recommended',
                message: 'High value cargo should have comprehensive insurance coverage specified.',
                field: 'cargo_packing.insurance_coverage_type',
                severity: 'medium',
                icon: '🛡️'
            });
        }
        
        return suggestions;
    }

    /**
     * Run all validation rules
     */
    function validateAll(state) {
        if (!state) return [];
        
        const allIssues = [
            ...checkSundayDeparture(state),
            ...checkHSCodeLogic(state),
            ...checkWeightVolumeRatio(state),
            ...checkContainerLogic(state),
            ...checkDangerousGoodsKeywords(state),
            ...checkIncotermLogic(state),
            ...checkTransitTime(state),
            ...checkInsuranceValue(state)
        ];
        
        // Sort by severity: high -> medium -> low
        const severityOrder = { high: 0, medium: 1, low: 2 };
        allIssues.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);
        
        return allIssues;
    }

    /**
     * Format date helper
     */
    function formatDate(date) {
        const options = { year: 'numeric', month: 'short', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // Public API
    return {
        validateAll,
        checkSundayDeparture,
        checkHSCodeLogic,
        checkWeightVolumeRatio,
        checkContainerLogic,
        checkDangerousGoodsKeywords,
        checkIncotermLogic,
        checkTransitTime,
        checkInsuranceValue
    };

})();

// Make ExpertRules available globally
window.ExpertRules = ExpertRules;

console.log('[ExpertRules] Module loaded successfully');
