/**
 * Scenario Classification Utility
 * 
 * ENGINE-FIRST: Classifies risk scenarios based on engine-provided data.
 * Never recomputes values - only analyzes what engine provides.
 * 
 * Scenario Types:
 * - FULL_RISK_AND_LOSS: Operational risk exists AND financial loss exposure exists
 * - OPERATIONAL_RISK_ONLY: Operational risk exists BUT no financial loss exposure
 * - NO_RISK_DETECTED: No operational risk detected
 * 
 * @module scenarioClassifier
 */

/**
 * Classify risk scenario based on risk score and financial metrics
 * @param {Object} data - Risk and financial data from backend
 * @param {number|null} data.riskScore - Overall risk score (0-10 or 0-100)
 * @param {Object} data.financial - Financial metrics object
 * @returns {Object} Scenario classification
 */
export function classifyScenario(data) {
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
    
    // CRITICAL: Check cargoValue first - if cargoValue > 0, we should calculate financial loss
    // even if current metrics are 0 (they may not have been calculated yet)
    const cargoValue = financial.cargoValue ?? 
                      data.shipment?.value_usd ?? 
                      data.shipment?.cargo_value ?? 
                      data.shipment?.cargoValue ?? 
                      null;
    const hasCargoValue = cargoValue != null && parseFloat(cargoValue) > 0;
    
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
    
    // IMPORTANT: If cargoValue > 0 but metrics are 0, still classify as FULL_RISK_AND_LOSS
    // because financial loss should be calculated (backend may not have calculated yet, or values are legitimately 0)
    // Only classify as OPERATIONAL_RISK_ONLY if cargoValue is 0 or missing
    if (hasCargoValue && !hasFinancialExposure) {
        // Cargo value exists but metrics are 0 - this could mean:
        // 1. Backend hasn't calculated yet (should show as FULL_RISK_AND_LOSS)
        // 2. Legitimately 0 loss (still show financial section)
        // So we classify as FULL_RISK_AND_LOSS to show financial section
        return {
            type: 'FULL_RISK_AND_LOSS',
            label: 'Full Risk & Loss',
            description: 'Operational and financial risk exposure detected',
            severity: 'standard'
        };
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
            label: 'OPERATIONAL RISK ONLY',
            description: 'No financial loss exposure detected for this shipment',
            severity: 'operational',
            subtitle: 'No financial loss exposure detected'
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
 * @param {Object} scenario - Result from classifyScenario()
 * @returns {Object} Badge configuration
 */
export function getScenarioBadge(scenario) {
    const badges = {
        'FULL_RISK_AND_LOSS': {
            label: 'Full Risk & Loss',
            className: 'scenario-badge-full',
            icon: '📊',
            color: 'var(--risk-medium, #ffcc00)'
        },
        'OPERATIONAL_RISK_ONLY': {
            label: 'OPERATIONAL RISK ONLY',
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
 * @param {Object} scenario - Result from classifyScenario()
 * @returns {Object} Empty state configuration
 */
export function getFinancialEmptyState(scenario) {
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

// Make available globally for browser environments
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
}
