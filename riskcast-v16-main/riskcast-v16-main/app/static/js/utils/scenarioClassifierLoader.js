/**
 * Scenario Classifier Loader
 * 
 * Makes scenarioClassifier utilities available globally in browser environment.
 * This ensures components can access scenario classification functions without
 * complex module imports in a potentially mixed module/script tag setup.
 */

(function() {
    'use strict';

    // Inline the core functions from scenarioClassifier.js
    // This ensures they're available even if the module doesn't load properly

    /**
     * Classify risk scenario based on risk score and financial metrics
     */
    function classifyScenario(data) {
        if (!data || typeof data !== 'object') {
            return {
                type: 'NO_RISK_DETECTED',
                label: 'No Risk Detected',
                description: 'No risk data available',
                severity: 'neutral'
            };
        }

        // Extract risk score - handle both 0-10 and 0-100 scales
        const riskScore = data.riskScore ?? 
                         data.overall?.riskScore ?? 
                         data.risk?.finalScore ?? 
                         data.overall_risk ?? 
                         null;

        // Normalize risk score to 0-10 scale if needed
        let normalizedRiskScore = null;
        if (riskScore !== null && riskScore !== undefined) {
            const num = parseFloat(riskScore);
            if (!isNaN(num)) {
                normalizedRiskScore = num > 10 ? num / 10 : num;
            }
        }

        // Extract financial data
        const financial = data.financial || {};
        const financialMetrics = [
            financial.expectedLoss ?? financial.meanLoss,
            financial.var95 ?? financial.p95,
            financial.cvar ?? financial.maxLoss ?? financial.maxObserved,
            financial.maxLoss ?? financial.maxObserved
        ].filter(v => v !== null && v !== undefined);

        // Check if any financial metric is non-zero
        const hasFinancialExposure = financialMetrics.length > 0 && 
                                     financialMetrics.some(v => {
                                         const num = parseFloat(v);
                                         return !isNaN(num) && num > 0;
                                     });

        // Check distribution array if available
        const distribution = financial.distribution;
        if (Array.isArray(distribution) && distribution.length > 0) {
            const distributionHasNonZero = distribution.some(v => {
                const num = parseFloat(v);
                return !isNaN(num) && num > 0;
            });
            if (distributionHasNonZero) {
                // Override: if distribution has non-zero values, we have financial exposure
                return {
                    type: 'FULL_RISK_AND_LOSS',
                    label: 'Full Risk & Loss',
                    description: 'Operational and financial risk exposure detected',
                    severity: 'standard'
                };
            }
        }

        // Classify scenario
        const hasOperationalRisk = normalizedRiskScore !== null && 
                                   normalizedRiskScore > 0;

        if (!hasOperationalRisk) {
            return {
                type: 'NO_RISK_DETECTED',
                label: 'No Risk Detected',
                description: 'No operational risk detected for this shipment',
                severity: 'neutral'
            };
        }

        if (hasOperationalRisk && hasFinancialExposure) {
            return {
                type: 'FULL_RISK_AND_LOSS',
                label: 'Full Risk & Loss',
                description: 'Operational and financial risk exposure detected',
                severity: 'standard'
            };
        }

        if (hasOperationalRisk && !hasFinancialExposure) {
            return {
                type: 'OPERATIONAL_RISK_ONLY',
                label: 'Operational Risk Only',
                description: 'No financial loss exposure detected for this shipment',
                severity: 'operational',
                subtitle: 'No financial loss exposure detected for this shipment'
            };
        }

        // Fallback
        return {
            type: 'NO_RISK_DETECTED',
            label: 'No Risk Detected',
            description: 'Insufficient data to classify scenario',
            severity: 'neutral'
        };
    }

    /**
     * Get scenario badge configuration for UI
     */
    function getScenarioBadge(scenario) {
        const badges = {
            'FULL_RISK_AND_LOSS': {
                label: 'Full Risk & Loss',
                className: 'scenario-badge-full',
                icon: '📊',
                color: 'var(--risk-medium, #ffcc00)'
            },
            'OPERATIONAL_RISK_ONLY': {
                label: 'Operational Risk Only',
                className: 'scenario-badge-operational',
                icon: '⚙️',
                color: 'var(--risk-low, #00ffc8)'
            },
            'NO_RISK_DETECTED': {
                label: 'No Risk Detected',
                className: 'scenario-badge-none',
                icon: '✓',
                color: 'var(--risk-low, #00ffc8)'
            }
        };

        return badges[scenario.type] || badges['NO_RISK_DETECTED'];
    }

    /**
     * Get financial empty state message based on scenario
     */
    function getFinancialEmptyState(scenario) {
        if (scenario.type === 'OPERATIONAL_RISK_ONLY') {
            return {
                title: 'Financial loss simulation not applicable',
                description: 'This scenario involves operational risk factors only',
                note: 'No financial loss exposure detected. Risk analysis focuses on operational factors such as delays, routing complexity, and service quality.',
                scenarioAware: true
            };
        }

        if (scenario.type === 'NO_RISK_DETECTED') {
            return {
                title: 'No financial loss simulated',
                description: 'No risk detected for this shipment',
                note: 'Risk analysis indicates minimal to no risk exposure',
                scenarioAware: true
            };
        }

        // Fallback (shouldn't happen for FULL_RISK_AND_LOSS, but handle gracefully)
        return {
            title: 'No financial loss simulated',
            description: 'Cargo value not provided or equal to zero',
            note: 'Risk analysis based on operational factors only',
            scenarioAware: false
        };
    }

    // Make available globally
    if (typeof window !== 'undefined') {
        if (!window.RISKCAST) {
            window.RISKCAST = {};
        }
        if (!window.RISKCAST.utils) {
            window.RISKCAST.utils = {};
        }
        window.RISKCAST.utils.scenarioClassifier = {
            classifyScenario,
            getScenarioBadge,
            getFinancialEmptyState
        };
        
        console.log('✅ RISKCAST Scenario Classifier utility loaded');
    }

    // Also export for module systems if needed
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            classifyScenario,
            getScenarioBadge,
            getFinancialEmptyState
        };
    }
})();

