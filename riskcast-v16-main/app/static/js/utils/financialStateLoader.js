/**
 * Financial State Utility Loader
 * 
 * Makes financialState utilities available globally for browser environments.
 * Can be loaded via script tag or imported as module.
 */

(function() {
    'use strict';

    // Load utility functions
    function analyzeFinancialState(financialData) {
        if (!financialData || typeof financialData !== 'object') {
            return {
                hasFinancialData: false,
                hasNonZeroImpact: false,
                zeroImpactReason: 'No financial data provided'
            };
        }

        const metrics = {
            expectedLoss: financialData.expectedLoss ?? financialData.meanLoss ?? null,
            var95: financialData.var95 ?? financialData.p95 ?? null,
            cvar: financialData.cvar ?? financialData.maxLoss ?? financialData.maxObserved ?? null,
            maxLoss: financialData.maxLoss ?? financialData.maxObserved ?? null,
            cargoValue: financialData.cargoValue ?? null,
            distribution: financialData.distribution ?? null
        };

        const hasFinancialData = Object.values(metrics).some(val => val !== null) || 
                                (Array.isArray(metrics.distribution) && metrics.distribution.length > 0);

        if (!hasFinancialData) {
            return {
                hasFinancialData: false,
                hasNonZeroImpact: false,
                zeroImpactReason: 'No financial data provided'
            };
        }

        const numericValues = [
            metrics.expectedLoss,
            metrics.var95,
            metrics.cvar,
            metrics.maxLoss
        ].filter(v => v !== null && v !== undefined);

        let distributionHasNonZero = false;
        if (Array.isArray(metrics.distribution) && metrics.distribution.length > 0) {
            distributionHasNonZero = metrics.distribution.some(v => {
                const num = parseFloat(v);
                return !isNaN(num) && num > 0;
            });
        }

        const allMetricsZero = numericValues.length === 0 || 
                              numericValues.every(v => {
                                  const num = parseFloat(v);
                                  return isNaN(num) || num === 0;
                              });

        const hasNonZeroImpact = distributionHasNonZero || !allMetricsZero;

        let zeroImpactReason = null;
        if (!hasNonZeroImpact) {
            if (metrics.cargoValue === null || metrics.cargoValue === undefined || parseFloat(metrics.cargoValue) === 0) {
                zeroImpactReason = 'Cargo value not provided or equal to zero';
            } else {
                zeroImpactReason = 'No financial loss simulated';
            }
        }

        return {
            hasFinancialData,
            hasNonZeroImpact,
            zeroImpactReason,
            metrics
        };
    }

    function isZeroImpactScenario(financialData) {
        const state = analyzeFinancialState(financialData);
        return !state.hasNonZeroImpact;
    }

    function getZeroImpactEmptyState(financialState) {
        const reason = financialState.zeroImpactReason || 'No financial loss simulated';
        
        return {
            title: 'No financial loss simulated',
            description: reason,
            note: 'Risk analysis based on operational factors only'
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
        window.RISKCAST.utils.financialState = {
            analyzeFinancialState,
            isZeroImpactScenario,
            getZeroImpactEmptyState
        };
    }

    // Export for module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = {
            analyzeFinancialState,
            isZeroImpactScenario,
            getZeroImpactEmptyState
        };
    }

    console.log('✅ Financial State Utility loaded');
})();

