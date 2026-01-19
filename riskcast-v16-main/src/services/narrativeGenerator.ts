/**
 * Narrative Generator Service
 * 
 * Generates personalized narratives for shipment risk assessments.
 * MUST be personalized - no generic statements allowed.
 */

import type { ResultsViewModel } from '../types/resultsViewModel';

interface NarrativeGeneratorInput {
  shipment: ResultsViewModel['overview']['shipment'];
  riskScore: ResultsViewModel['overview']['riskScore'];
  breakdown: ResultsViewModel['breakdown'];
  financial: ResultsViewModel['loss'] | null;
  logistics?: ResultsViewModel['logistics'];
}

/**
 * Format currency value
 */
function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`;
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

/**
 * Get driver explanation based on layer name and shipment context
 */
function getDriverExplanation(
  layerName: string, 
  contribution: number,
  shipment: NarrativeGeneratorInput['shipment']
): string {
  const cargoType = shipment.cargoType || shipment.cargo || '';
  const containerType = shipment.containerType || shipment.container || '';
  const transitDays = shipment.transitTime || 0;
  
  // Climate Risk
  if (layerName.toLowerCase().includes('climate') || layerName.toLowerCase().includes('weather')) {
    if (transitDays > 30) {
      return `Extended ${transitDays}-day transit increases exposure to weather events`;
    }
    return `Seasonal weather patterns affect this route`;
  }
  
  // Port Congestion
  if (layerName.toLowerCase().includes('port') || layerName.toLowerCase().includes('congestion')) {
    return `Port congestion at origin/destination increases delay risk`;
  }
  
  // Cargo Sensitivity
  if (layerName.toLowerCase().includes('cargo') || layerName.toLowerCase().includes('sensitivity')) {
    if (cargoType.toLowerCase().includes('electronic')) {
      return `Electronics are sensitive to moisture and temperature changes`;
    }
    if (cargoType.toLowerCase().includes('perishable') || cargoType.toLowerCase().includes('food')) {
      return `Perishable cargo requires temperature control throughout transit`;
    }
    return `Cargo type (${cargoType}) has specific handling requirements`;
  }
  
  // Carrier Risk
  if (layerName.toLowerCase().includes('carrier') || layerName.toLowerCase().includes('transport')) {
    return `Carrier reliability and route experience affect risk`;
  }
  
  // Default
  return `This factor contributes ${contribution.toFixed(0)}% to overall risk`;
}

/**
 * Generate seasonal alert if applicable
 */
function generateSeasonalAlert(
  logistics: ResultsViewModel['logistics'] | undefined,
  shipment: NarrativeGeneratorInput['shipment']
): string {
  if (!logistics?.routeSeasonality) {
    return '';
  }
  
  const seasonality = logistics.routeSeasonality;
  if (seasonality.riskLevel === 'LOW') {
    return '';
  }
  
  const transitDays = shipment.transitTime || 0;
  const season = seasonality.season;
  const riskLevel = seasonality.riskLevel;
  
  // Determine ocean/region from route
  const pol = typeof shipment.pol === 'string' ? shipment.pol : shipment.pol.code || '';
  const pod = typeof shipment.pod === 'string' ? shipment.pod : shipment.pod.code || '';
  
  let ocean = 'Pacific';
  if (pol.includes('EU') || pod.includes('EU') || pol.includes('GB') || pod.includes('GB')) {
    ocean = 'Atlantic';
  }
  
  const factors = seasonality.factors.map(f => f.factor).join(', ');
  
  return `**SEASONAL ALERT:**\n` +
    `Your ${transitDays}-day transit crosses the ${ocean} Ocean during ${season}, ` +
    `when ${factors} conditions increase risk by ${riskLevel === 'HIGH' ? 'elevated' : 'moderate'} levels.`;
}

/**
 * Generate action recommendations with cost/benefit
 */
function generateActionRecommendations(input: NarrativeGeneratorInput): string {
  const { shipment, riskScore, breakdown, financial, logistics } = input;
  const cargoType = shipment.cargoType || shipment.cargo || '';
  const cargoValue = typeof shipment.cargoValue === 'number' 
    ? shipment.cargoValue 
    : shipment.cargoValue?.amount || 0;
  const transitDays = shipment.transitTime || 0;
  
  const actions: Array<{ action: string; cost: number; reduction: number; rationale: string }> = [];
  
  // Electronics-specific actions
  if (cargoType.toLowerCase().includes('electronic')) {
    actions.push({
      action: 'Add desiccant packs',
      cost: 200,
      reduction: 40,
      rationale: 'Reduces moisture damage risk from temperature cycling',
    });
    actions.push({
      action: 'Use humidity indicator cards',
      cost: 50,
      reduction: 20,
      rationale: 'Enables insurance claim documentation for moisture damage',
    });
  }
  
  // Long transit actions
  if (transitDays > 30) {
    actions.push({
      action: 'Purchase delay rider insurance',
      cost: 1500,
      reduction: 25,
      rationale: `Covers delays > 7 days (${logistics?.delayProbabilities?.p7days ? (logistics.delayProbabilities.p7days * 100).toFixed(0) : '22'}% trigger probability)`,
    });
  }
  
  // High value actions
  if (cargoValue > 200000) {
    actions.push({
      action: 'Upgrade to ICC(A) coverage',
      cost: cargoValue * 0.001, // 0.1% of cargo value
      reduction: 15,
      rationale: 'Broadest coverage for high-value cargo',
    });
  }
  
  // Packaging recommendations from logistics
  if (logistics?.packagingRecommendations && logistics.packagingRecommendations.length > 0) {
    logistics.packagingRecommendations.slice(0, 2).forEach(rec => {
      actions.push({
        action: rec.item,
        cost: rec.cost,
        reduction: rec.riskReduction,
        rationale: rec.rationale,
      });
    });
  }
  
  // Default actions if none generated
  if (actions.length === 0) {
    if (riskScore.score >= 60) {
      actions.push({
        action: 'Review insurance coverage options',
        cost: 0,
        reduction: 10,
        rationale: 'Ensure adequate coverage for identified risks',
      });
    }
    actions.push({
      action: 'Continue monitoring shipment',
      cost: 0,
      reduction: 5,
      rationale: 'Standard monitoring applies',
    });
  }
  
  // Format actions
  return actions.map((action, idx) => 
    `${idx + 1}. **${action.action}** — Cost: ${formatCurrency(action.cost)}, Risk Reduction: ${action.reduction}%\n   ${action.rationale}`
  ).join('\n\n');
}

/**
 * Generate personalized narrative
 * 
 * MUST be personalized - no generic statements allowed.
 */
export function generatePersonalizedNarrative(input: NarrativeGeneratorInput): string {
  const { shipment, riskScore, breakdown, financial, logistics } = input;
  
  // Extract key information
  const cargoType = shipment.cargoType || shipment.cargo || 'cargo';
  const cargoValue = typeof shipment.cargoValue === 'number' 
    ? shipment.cargoValue 
    : shipment.cargoValue?.amount || 0;
  const pol = typeof shipment.pol === 'string' ? shipment.pol : shipment.pol.name || shipment.pol.code || 'Origin';
  const pod = typeof shipment.pod === 'string' ? shipment.pod : shipment.pod.name || shipment.pod.code || 'Destination';
  const carrier = shipment.carrier || 'Ocean Carrier';
  const riskLevel = riskScore.level.toUpperCase();
  const riskScoreValue = Math.round(riskScore.score);
  
  // Opening paragraph - MUST be personalized
  const opening = `Your **${cargoType.toUpperCase()}** shipment ` +
    `(value: ${formatCurrency(cargoValue)}) ` +
    `from **${pol}** to **${pod}** ` +
    `via **${carrier}** has a **${riskLevel}** risk score ` +
    `(${riskScoreValue}/100).`;
  
  // Why section - MUST mention top 3 drivers
  const topLayers = breakdown.layers
    .filter(l => l.contribution > 0)
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 3);
  
  if (topLayers.length === 0) {
    // Fallback to drivers if layers not available
    const topDrivers = breakdown.layers.slice(0, 3);
    const whyLines = topDrivers.length > 0
      ? topDrivers.map(l => 
          `• **${l.name}**: ${l.contribution.toFixed(0)}% — ${getDriverExplanation(l.name, l.contribution, shipment)}`
        ).join('\n')
      : '• Risk factors have been assessed based on available data';
    
    return `${opening}\n\n**WHY THIS SCORE:**\n${whyLines}`;
  }
  
  const whyLines = topLayers.map(l => 
    `• **${l.name}**: ${l.contribution.toFixed(0)}% — ${getDriverExplanation(l.name, l.contribution, shipment)}`
  ).join('\n');
  
  // Seasonal alert - conditional
  const seasonalAlert = generateSeasonalAlert(logistics, shipment);
  
  // Actions - MUST have cost/benefit
  const actions = generateActionRecommendations(input);
  
  // Loss expectations
  const lossExpectations = financial && financial.expectedLoss > 0
    ? `**LOSS EXPECTATIONS:**\n` +
      `• Most likely: ${formatCurrency(financial.expectedLoss)} (50th percentile)\n` +
      `• Bad case: ${formatCurrency(financial.p95)} (95th percentile)\n` +
      `• Worst case: ${formatCurrency(financial.p99)} (99th percentile)`
    : '';
  
  // Combine all sections
  const sections = [
    opening,
    `**WHY THIS SCORE:**\n${whyLines}`,
    seasonalAlert,
    `**RECOMMENDED ACTIONS:**\n${actions}`,
    lossExpectations,
  ].filter(Boolean);
  
  return sections.join('\n\n');
}

/**
 * Generate narrative view model
 */
export function generateNarrativeViewModel(viewModel: ResultsViewModel): ResultsViewModel['narrative'] {
  const personalizedSummary = generatePersonalizedNarrative({
    shipment: viewModel.overview.shipment,
    riskScore: viewModel.overview.riskScore,
    breakdown: viewModel.breakdown,
    financial: viewModel.loss,
    logistics: viewModel.logistics,
  });
  
  // Extract why this score
  const whyThisScore = viewModel.overview.reasoning.explanation || 
    `Risk score of ${viewModel.overview.riskScore.score.toFixed(0)}/100 is based on analysis of ${viewModel.breakdown.layers.length} risk layers.`;
  
  // Top risk factors
  const topRiskFactors = viewModel.breakdown.layers
    .filter(l => l.contribution > 0)
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 5)
    .map(l => ({
      factor: l.name,
      contribution: l.contribution,
    }));
  
  // Action items from scenarios
  const actionItems = viewModel.scenarios
    .filter(s => s.isRecommended || s.rank <= 3)
    .slice(0, 4)
    .map(s => ({
      action: s.title,
      priority: s.isRecommended ? 'immediate' as const : 
                s.rank <= 2 ? 'short-term' as const : 'long-term' as const,
    }));
  
  // Source attribution
  const dataPointCount = viewModel.breakdown.layers.length + viewModel.drivers.length;
  const sourceAttribution = `Based on ${dataPointCount} data points from risk engine analysis`;
  
  return {
    personalizedSummary,
    whyThisScore,
    topRiskFactors,
    actionItems,
    sourceAttribution,
  };
}
