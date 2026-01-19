import type { LayerData, LayerStatus, RiskLevel } from '../types';

let layerSeq = 1;

function statusForRiskLevel(level: RiskLevel): LayerStatus {
  if (level === 'HIGH') return 'ALERT';
  if (level === 'MEDIUM') return 'WARNING';
  return 'OK';
}

function scoreForRiskLevel(level: RiskLevel): number {
  if (level === 'HIGH') return 82;
  if (level === 'MEDIUM') return 55;
  return 22;
}

export function createMockLayer(overrides: Partial<LayerData> & Pick<LayerData, 'name'>): LayerData {
  return {
    name: overrides.name,
    score: overrides.score ?? 50,
    contribution: overrides.contribution ?? 10,
    status: overrides.status ?? 'NORMAL',
    notes: overrides.notes ?? '—',
    confidence: overrides.confidence,
    dataSource: overrides.dataSource,
    lastUpdated: overrides.lastUpdated,
    trace: overrides.trace,
  };
}

export function createMockLayers(config?: {
  riskLevel?: RiskLevel;
  layerCount?: number;
  baseNames?: string[];
}): LayerData[] {
  const riskLevel = config?.riskLevel ?? 'MEDIUM';
  const layerCount = config?.layerCount ?? 6;

  const defaultNames = [
    'Geopolitical Risk',
    'Port Congestion',
    'Weather Risk',
    'Carrier Reliability',
    'Regulatory Risk',
    'Financial Risk',
  ];

  const names = (config?.baseNames?.length ? config.baseNames : defaultNames)
    .slice(0, layerCount)
    .concat(Array.from({ length: Math.max(0, layerCount - defaultNames.length) }, () => `Custom Layer ${layerSeq++}`));

  const baseContribution = Math.floor(100 / Math.max(1, layerCount));
  const remainder = 100 - baseContribution * layerCount;

  return names.slice(0, layerCount).map((name, idx) => {
    const contribution = baseContribution + (idx < remainder ? 1 : 0);
    const score = scoreForRiskLevel(riskLevel) + (idx % 3) * 3;
    return createMockLayer({
      name,
      contribution,
      score,
      status: statusForRiskLevel(riskLevel),
      notes: `Mock notes for ${name}`,
      confidence: 60 + (idx % 5) * 5,
    });
  });
}

