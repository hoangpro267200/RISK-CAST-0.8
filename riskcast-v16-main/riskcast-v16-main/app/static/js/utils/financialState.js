/**
 * Financial State Utility
 * 
 * ENGINE-FIRST: Determines semantic financial state from backend data.
 * Never recomputes financial values - only analyzes what engine provides.
 * 
 * @module financialState
 */

/**
 * Analyze financial data to determine semantic state
 * @param {Object} financialData - Financial data from backend
 * @returns {Object} Financial state with semantic flags
 */
export function analyzeFinancialState(financialData) {
    if (!financialData || typeof financialData !== 'object') {
        return {
            hasFinancialData: false,
            hasNonZeroImpact: false,
            zeroImpactReason: 'No financial data provided'
        };
    }

    // Extract key financial metrics
    const metrics = {
        expectedLoss: financialData.expectedLoss ?? financialData.meanLoss ?? null,
        var95: financialData.var95 ?? financialData.p95 ?? null,
        cvar: financialData.cvar ?? financialData.maxLoss ?? financialData.maxObserved ?? null,
        maxLoss: financialData.maxLoss ?? financialData.maxObserved ?? null,
        cargoValue: financialData.cargoValue ?? null,
        // Distribution array if available
        distribution: financialData.distribution ?? null
    };

    // Check if we have any financial data structure
    const hasFinancialData = Object.values(metrics).some(val => val !== null) || 
                            (Array.isArray(metrics.distribution) && metrics.distribution.length > 0);

    if (!hasFinancialData) {
        return {
            hasFinancialData: false,
            hasNonZeroImpact: false,
            zeroImpactReason: 'No financial data provided'
        };
    }

    // Check if all numeric values are zero or null
    const numericValues = [
        metrics.expectedLoss,
        metrics.var95,
        metrics.cvar,
        metrics.maxLoss
    ].filter(v => v !== null && v !== undefined);

    // Check distribution array if available
    let distributionHasNonZero = false;
    if (Array.isArray(metrics.distribution) && metrics.distribution.length > 0) {
        distributionHasNonZero = metrics.distribution.some(v => {
            const num = parseFloat(v);
            return !isNaN(num) && num > 0;
        });
    }

    // Check if all numeric metrics are zero
    const allMetricsZero = numericValues.length === 0 || 
                          numericValues.every(v => {
                              const num = parseFloat(v);
                              return isNaN(num) || num === 0;
                          });

    // Determine if there's non-zero impact
    const hasNonZeroImpact = distributionHasNonZero || !allMetricsZero;

    // Determine reason for zero impact
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

/**
 * Check if financial data represents a zero-impact scenario
 * Convenience wrapper for hasNonZeroImpact check
 * 
 * @param {Object} financialData - Financial data from backend
 * @returns {boolean} True if all values are zero/null
 */
export function isZeroImpactScenario(financialData) {
    const state = analyzeFinancialState(financialData);
    return !state.hasNonZeroImpact;
}

/**
 * Get empty state message for zero-impact scenario
 * @param {Object} financialState - Result from analyzeFinancialState()
 * @returns {Object} Empty state UI content
 */
export function getZeroImpactEmptyState(financialState) {
    const reason = financialState.zeroImpactReason || 'No financial loss simulated';
    
    return {
        title: 'No financial loss simulated',
        description: reason,
        note: 'Risk analysis based on operational factors only'
    };
}

// Make available globally for browser environments
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

