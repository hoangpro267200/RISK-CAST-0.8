import type { RiskAnalysisResult, RiskLevel, Scenario, DecisionSignal } from '../types';
import { createMockShipment } from './shipment.fixture';
import { createMockLayers } from './layers.fixture';
import { createMockTraces } from './traces.fixture';

export function createMockScenarios(count = 2): Scenario[] {
  const base: Scenario[] = [
    {
      title: 'Reroute via alternate hub',
      riskReduction: 12,
      costImpact: 4.5,
      description: 'Reduce geopolitics exposure.',
      feasibility: 70,
    },
    {
      title: 'Delay departure 48h',
      riskReduction: 5,
      costImpact: 1.2,
      description: 'Avoid congestion peak.',
      feasibility: 85,
    },
  ];
  if (count <= base.length) return base.slice(0, count);
  return base.concat(
    Array.from({ length: count - base.length }, (_, i) => ({
      title: `Scenario ${i + 3}`,
      riskReduction: 3 + (i % 5),
      costImpact: 0.8 + (i % 4) * 0.6,
      description: 'Generated scenario.',
      feasibility: 60 + (i % 4) * 10,
    }))
  );
}

export function createMockDecisionSignal(riskLevel: RiskLevel): DecisionSignal {
  const recommendation = riskLevel === 'HIGH' ? 'BUY' : riskLevel === 'MEDIUM' ? 'OPTIONAL' : 'SKIP';
  return {
    recommendation,
    rationale:
      recommendation === 'BUY'
        ? 'Coverage recommended due to elevated tail risk.'
        : recommendation === 'OPTIONAL'
          ? 'Consider coverage depending on risk appetite.'
          : 'Coverage likely unnecessary given low risk.',
    providers: [
      { name: 'Provider A', premium: 12000, fitScore: 0.78 },
      { name: 'Provider B', premium: 9800, fitScore: 0.71 },
    ],
  };
}

export function createMockRiskAnalysis(config?: {
  riskLevel?: RiskLevel;
  layerCount?: number;
  includeTraces?: boolean;
  includeDrivers?: boolean;
}): RiskAnalysisResult {
  const riskLevel = config?.riskLevel ?? 'MEDIUM';
  const layerCount = config?.layerCount ?? 6;
  const layers = createMockLayers({ riskLevel, layerCount });
  const layerNames = layers.map((l) => l.name);
  const score = riskLevel === 'HIGH' ? 78 : riskLevel === 'MEDIUM' ? 55 : 22;

  return {
    shipment: createMockShipment({ dataConfidence: 0.65 }),
    riskScore: {
      overallScore: score,
      riskLevel,
      verdict:
        riskLevel === 'HIGH' ? 'High risk — review mitigations.' : riskLevel === 'MEDIUM' ? 'Moderate risk.' : 'Low risk.',
      dataConfidence: 0.68,
      engineVersion: 'engine-1.0.0',
    },
    layers,
    decisionSignal: createMockDecisionSignal(riskLevel),
    timing: { optimalWindow: '2025-01-03 → 2025-01-06', riskReduction: riskLevel === 'HIGH' ? 6 : 2 },
    scenarios: createMockScenarios(2),
    financial: null,
    aiNarrative: {
      executiveSummary: `Overall risk is ${riskLevel.toLowerCase()}.`,
      keyInsights: layers.slice(0, 2).map((l) => `${l.name} is a key driver.`),
      actionItems: ['Review decision recommendations.', 'Inspect evidence layers for key drivers.'],
      riskDrivers: layers.slice(0, 3).map((l) => l.name),
      confidenceNotes: 'Confidence moderate; some sources may be stale.',
    },
    timeline: [],
    riskOverTime: [],
    riskScenarioProjections: [],
    dataReliability: [],
    drivers:
      config?.includeDrivers === false
        ? undefined
        : layers.slice(0, Math.min(5, layers.length)).map((l, idx) => ({
            id: `drv-${idx + 1}`,
            layerName: l.name,
            label: `Driver ${idx + 1} for ${l.name}`,
            contributionPct: Math.max(5, 40 - idx * 6),
            direction: 'increase' as const,
            confidence: 0.6 + (idx % 3) * 0.1,
            evidence: { source: 'model', note: `Model evidence for ${l.name}` },
          })),
    traces: createMockTraces({ layerNames, includeTraces: config?.includeTraces ?? true }),
  };
}

export const mockRiskData_HighRisk: RiskAnalysisResult = createMockRiskAnalysis({
  riskLevel: 'HIGH',
  includeTraces: true,
});
export const mockRiskData_LowRisk: RiskAnalysisResult = createMockRiskAnalysis({
  riskLevel: 'LOW',
  includeTraces: true,
});
export const mockRiskData_PartialData: RiskAnalysisResult = createMockRiskAnalysis({
  riskLevel: 'HIGH',
  includeTraces: false,
});
export const mockRiskData_EmptyLayers: RiskAnalysisResult = {
  ...createMockRiskAnalysis({ riskLevel: 'MEDIUM', includeTraces: false }),
  layers: [],
};
export const mockRiskData_LargeDataset: RiskAnalysisResult = createMockRiskAnalysis({
  riskLevel: 'MEDIUM',
  layerCount: 120,
  includeTraces: false,
});

