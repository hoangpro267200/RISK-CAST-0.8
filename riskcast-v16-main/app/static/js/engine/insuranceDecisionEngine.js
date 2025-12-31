/**
 * Insurance Decision Engine
 * 
 * Pure, deterministic insurance recommendation algorithm based on risk analytics.
 * This engine implements business rules for insurance decisions (BUY/OPTIONAL/SKIP).
 * 
 * ARCHITECTURE: ENGINE-FIRST
 * This is a decision engine module that operates independently of UI concerns.
 * It contains business logic, decision rules, and deterministic computations.
 * 
 * @file engine/insuranceDecisionEngine.js
 */

/**
 * NOTE:
 * This engine provides decision support recommendations only.
 * It does NOT replace insurance underwriting, pricing, or policy drafting.
 */

/**
 * Insurance Recommendation Algorithm
 * Pure, deterministic decision logic based on risk analytics
 * 
 * @param {Object} summaryData - Summary data with risk metrics
 * @param {number} summaryData.finalRiskScore - Final risk score (0-100)
 * @param {string} summaryData.riskLevel - Risk level (LOW|MEDIUM|HIGH|CRITICAL)
 * @param {Object} summaryData.lossMetrics - Loss metrics
 * @param {number} summaryData.lossMetrics.p95 - P95 VaR (USD)
 * @param {number} summaryData.lossMetrics.p99 - P99 CVaR (USD)
 * @param {number} summaryData.lossMetrics.tailContribution - Tail risk contribution (%)
 * @param {Object} summaryData.shipmentProfile - Shipment profile
 * @param {number} summaryData.shipmentProfile.value_usd - Shipment value (USD)
 * @param {string} summaryData.shipmentProfile.incoterm - Incoterm
 * @param {string} summaryData.shipmentProfile.route - Route string
 * @param {string} summaryData.shipmentProfile.cargo - Cargo type
 * @param {number} summaryData.uncertaintyLevel - Uncertainty/confidence (0-1)
 * @returns {Object|null} Insurance decision or null if inputs missing
 */
export function recommendInsurance(summaryData) {
  // Safety: Return null if required inputs missing
  if (!summaryData || typeof summaryData !== 'object') {
    return null;
  }

  const finalRiskScore = summaryData.finalRiskScore;
  const riskLevel = summaryData.riskLevel;
  const lossMetrics = summaryData.lossMetrics || {};
  const shipmentProfile = summaryData.shipmentProfile || {};
  const uncertaintyLevel = summaryData.uncertaintyLevel !== undefined ? summaryData.uncertaintyLevel : 0.8;

  // Validate required inputs
  if (finalRiskScore === undefined || finalRiskScore === null ||
      !riskLevel || typeof riskLevel !== 'string') {
    return null;
  }

  const p95 = lossMetrics.p95 || 0;
  const p99 = lossMetrics.p99 || 0;
  const tailContribution = lossMetrics.tailContribution || 0;
  const cargoValue = shipmentProfile.value_usd || 0;
  const route = shipmentProfile.route || '';
  const incoterm = shipmentProfile.incoterm || '';
  const cargoType = shipmentProfile.cargo || '';

  // Normalize risk level
  const riskLevelUpper = riskLevel.toUpperCase();
  const isHighRisk = riskLevelUpper === 'HIGH' || riskLevelUpper === 'CRITICAL' || finalRiskScore >= 70;
  const isMediumRisk = riskLevelUpper === 'MEDIUM' || (finalRiskScore >= 40 && finalRiskScore < 70);
  const isLowRisk = riskLevelUpper === 'LOW' || finalRiskScore < 40;

  // Decision: BUY | OPTIONAL | SKIP
  let action;
  let coverageType;
  const decisionTrace = [];

  // Rule 1: HIGH/CRITICAL risk → BUY
  if (isHighRisk) {
    action = 'BUY';
    decisionTrace.push(`Risk level ${riskLevelUpper} (score: ${finalRiskScore.toFixed(1)}) requires mandatory insurance`);
    
    // Determine coverage type based on tail risk
    if (tailContribution >= 25 || p99 > p95 * 2) {
      coverageType = 'TAIL_RISK';
      decisionTrace.push(`High tail risk (${tailContribution.toFixed(1)}%) requires tail risk coverage`);
    } else if (finalRiskScore >= 80 || riskLevelUpper === 'CRITICAL') {
      coverageType = 'FULL';
      decisionTrace.push(`Critical risk profile requires comprehensive coverage`);
    } else {
      coverageType = 'STANDARD';
      decisionTrace.push(`Standard coverage sufficient for high-risk profile`);
    }
  }
  // Rule 2: MEDIUM risk + high shipment value → OPTIONAL
  else if (isMediumRisk) {
    if (cargoValue >= 500000) {
      action = 'OPTIONAL';
      coverageType = 'STANDARD';
      decisionTrace.push(`Medium risk (score: ${finalRiskScore.toFixed(1)}) with high-value cargo ($${(cargoValue / 1000).toFixed(0)}K) suggests optional coverage`);
    } else if (tailContribution >= 20) {
      action = 'OPTIONAL';
      coverageType = 'STANDARD';
      decisionTrace.push(`Medium risk with elevated tail risk (${tailContribution.toFixed(1)}%) suggests optional coverage`);
    } else {
      action = 'OPTIONAL';
      coverageType = 'BASIC';
      decisionTrace.push(`Medium risk (score: ${finalRiskScore.toFixed(1)}) suggests basic optional coverage`);
    }
  }
  // Rule 3: LOW risk + low loss tail → SKIP
  else {
    if (tailContribution < 15 && p99 < 100000 && cargoValue < 500000) {
      action = 'SKIP';
      coverageType = 'BASIC';
      decisionTrace.push(`Low risk (score: ${finalRiskScore.toFixed(1)}) with low tail exposure suggests insurance may be unnecessary`);
    } else {
      action = 'OPTIONAL';
      coverageType = 'BASIC';
      decisionTrace.push(`Low risk profile, basic optional coverage if desired`);
    }
  }

  // Provider recommendation based on scored provider model
  const providerCandidates = [
    {
      name: 'Asia-Pacific Specialized',
      routeFit: 0,
      cargoFit: 0,
      stability: 0.75
    },
    {
      name: 'European Trade Provider',
      routeFit: 0,
      cargoFit: 0,
      stability: 0.80
    },
    {
      name: 'Trans-Pacific Provider',
      routeFit: 0,
      cargoFit: 0,
      stability: 0.70
    },
    {
      name: 'Standard Provider',
      routeFit: 0.5,
      cargoFit: 0.5,
      stability: 0.65
    }
  ];

  // Calculate route fit
  const routeUpper = route ? route.toUpperCase() : '';
  providerCandidates.forEach(provider => {
    const nameUpper = provider.name.toUpperCase();
    if (nameUpper.includes('ASIA') && (routeUpper.includes('ASIA') || routeUpper.includes('SHANGHAI') || routeUpper.includes('SINGAPORE'))) {
      provider.routeFit = 0.95;
    } else if (nameUpper.includes('EUROPE') && (routeUpper.includes('EUROPE') || routeUpper.includes('ROTTERDAM') || routeUpper.includes('HAMBURG'))) {
      provider.routeFit = 0.95;
    } else if (nameUpper.includes('PACIFIC') && (routeUpper.includes('AMERICA') || routeUpper.includes('US') || routeUpper.includes('USA'))) {
      provider.routeFit = 0.95;
    } else if (nameUpper.includes('STANDARD')) {
      provider.routeFit = 0.5;
    } else {
      provider.routeFit = 0.3;
    }
  });

  // Calculate cargo fit
  const cargoUpper = cargoType ? cargoType.toUpperCase() : '';
  const isElectronics = cargoUpper.includes('ELECTRONIC') || cargoUpper.includes('FRAGILE') || cargoUpper.includes('HIGH-VALUE');
  providerCandidates.forEach(provider => {
    const nameUpper = provider.name.toUpperCase();
    if (isElectronics && (nameUpper.includes('ASIA') || nameUpper.includes('PACIFIC'))) {
      provider.cargoFit = 0.90;
    } else if (isElectronics) {
      provider.cargoFit = 0.70;
    } else if (nameUpper.includes('STANDARD')) {
      provider.cargoFit = 0.60;
    } else {
      provider.cargoFit = 0.75;
    }
  });

  // Adjust stability based on risk level
  providerCandidates.forEach(provider => {
    if (isHighRisk) {
      provider.stability = Math.min(0.95, provider.stability + 0.10);
    } else if (isLowRisk) {
      provider.stability = Math.max(0.60, provider.stability - 0.05);
    }
  });

  // Calculate scores and select best provider
  providerCandidates.forEach(provider => {
    provider.score = 0.4 * provider.routeFit + 0.3 * provider.cargoFit + 0.3 * provider.stability;
  });

  const bestProvider = providerCandidates.reduce((best, current) => 
    current.score > best.score ? current : best
  );

  // Build reason
  let reasonParts = [];
  if (bestProvider.routeFit >= 0.9) {
    reasonParts.push(`optimal route specialization for ${route || 'specified route'}`);
  } else if (bestProvider.routeFit >= 0.5) {
    reasonParts.push(`adequate route coverage`);
  }
  
  if (bestProvider.cargoFit >= 0.85) {
    reasonParts.push(`specialized expertise for ${cargoType || 'cargo type'}`);
  } else if (bestProvider.cargoFit >= 0.6) {
    reasonParts.push(`suitable for cargo profile`);
  }
  
  if (bestProvider.stability >= 0.8) {
    reasonParts.push(`high stability for ${riskLevelUpper} risk environment`);
  } else if (bestProvider.stability >= 0.7) {
    reasonParts.push(`stable performance for current risk level`);
  }

  const recommendedProvider = {
    name: bestProvider.name,
    score: Math.round(bestProvider.score * 100) / 100,
    reason: reasonParts.length > 0 ? reasonParts.join(', ') : 'Standard coverage available'
  };

  // Confidence calculation (based on data completeness)
  let confidence = uncertaintyLevel;
  if (p95 > 0 && p99 > 0) {
    confidence = Math.min(0.95, confidence + 0.1); // Loss metrics available
  }
  if (cargoValue > 0) {
    confidence = Math.min(0.95, confidence + 0.05); // Cargo value known
  }
  if (route && route !== 'Route not specified') {
    confidence = Math.min(0.95, confidence + 0.05); // Route specified
  }

  // Distribution stability adjustment
  const distributionSpread = p95 > 0 ? (p99 - p95) / p95 : 0;
  if (distributionSpread <= 1.2) {
    confidence = confidence * 1.05;
  } else if (distributionSpread >= 2.0) {
    confidence = confidence * 0.9;
  }
  confidence = Math.max(0.5, Math.min(0.95, confidence));

  // Coverage intensity calculation
  let recommendedCoverageRatio;
  if (isHighRisk && tailContribution >= 25) {
    recommendedCoverageRatio = Math.max(0.7, Math.min(0.9, 0.7 + (tailContribution - 25) / 100));
  } else if (isHighRisk) {
    recommendedCoverageRatio = 0.6;
  } else if (isMediumRisk && cargoValue >= 500000) {
    recommendedCoverageRatio = Math.max(0.4, Math.min(0.6, 0.4 + (cargoValue - 500000) / 10000000));
  } else if (isMediumRisk) {
    recommendedCoverageRatio = Math.max(0.3, Math.min(0.4, 0.3 + tailContribution / 100));
  } else {
    recommendedCoverageRatio = Math.max(0.2, Math.min(0.3, 0.2 + tailContribution / 200));
  }
  recommendedCoverageRatio = Math.max(0.2, Math.min(0.9, recommendedCoverageRatio));

  // Incoterm-based micro adjustment
  const incotermUpper = incoterm ? incoterm.toUpperCase() : '';
  let incotermAdjustment = 0;
  if (incotermUpper === 'EXW' || incotermUpper === 'FOB') {
    incotermAdjustment = 0.05;
    decisionTrace.push(`Incoterm ${incotermUpper} indicates shipper bears additional logistics risk, recommending slightly higher coverage ratio`);
    confidence = Math.max(0.5, Math.min(0.95, confidence + 0.02));
  } else if (incotermUpper === 'CIF') {
    incotermAdjustment = -0.05;
    decisionTrace.push(`Incoterm ${incotermUpper} typically includes insurance upstream, recommending slightly lower coverage ratio`);
    confidence = Math.max(0.5, Math.min(0.95, confidence + 0.01));
  }
  
  recommendedCoverageRatio = Math.max(0.2, Math.min(0.9, recommendedCoverageRatio + incotermAdjustment));
  
  const maxCoverageLimit = cargoValue > 0 ? cargoValue * recommendedCoverageRatio : 0;

  // Build rationale
  const rationale = `Risk assessment (${riskLevelUpper}, score: ${finalRiskScore.toFixed(1)}) ` +
                   (p99 > 0 ? `with P99 exposure of $${(p99 / 1000).toFixed(0)}K ` : '') +
                   `${action === 'BUY' ? 'requires' : action === 'OPTIONAL' ? 'suggests' : 'indicates insurance may not be necessary'}. ` +
                   recommendedProvider.reason;

  return {
    action: action,
    coverageType: coverageType,
    recommendedProvider: recommendedProvider,
    confidence: Math.round(confidence * 100) / 100,
    rationale: rationale,
    decisionTrace: decisionTrace,
    coverageIntensity: {
      recommendedCoverageRatio: Math.round(recommendedCoverageRatio * 1000) / 1000,
      maxCoverageLimit: Math.round(maxCoverageLimit)
    }
  };
}
