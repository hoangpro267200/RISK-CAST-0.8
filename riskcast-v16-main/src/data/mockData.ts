import type { RiskAnalysisResult } from '../types';

export const mockRiskData: RiskAnalysisResult = {
  shipment: {
    shipmentId: 'SH-2025-001',
    route: {
      pol: 'Shanghai',
      pod: 'Los Angeles',
    },
    carrier: 'Maersk Line',
    etd: '2025-01-15',
    eta: '2025-02-20',
    dataConfidence: 0.87,
    lastUpdated: '2025-01-10T10:30:00Z',
  },
  riskScore: {
    overallScore: 68,
    riskLevel: 'MEDIUM',
    verdict: 'Moderate risk - recommend insurance coverage',
    dataConfidence: 0.87,
  },
  layers: [
    {
      name: 'Transport Risk',
      score: 72,
      contribution: 28,
      status: 'WARNING',
      notes: 'Elevated congestion at destination port',
      confidence: 85,
    },
    {
      name: 'Weather Risk',
      score: 45,
      contribution: 15,
      status: 'OK',
      notes: 'Normal seasonal patterns',
      confidence: 90,
    },
    {
      name: 'Geopolitical Risk',
      score: 55,
      contribution: 20,
      status: 'WARNING',
      notes: 'Regional tensions may affect routing',
      confidence: 75,
    },
  ],
  decisionSignal: {
    recommendation: 'BUY',
    rationale: 'Moderate risk profile with manageable mitigation costs',
    providers: [
      {
        name: 'Provider A',
        premium: 1250,
        fitScore: 0.85,
      },
    ],
  },
  timing: {
    optimalWindow: '2025-01-20 to 2025-01-25',
    riskReduction: 8,
  },
  scenarios: [
    {
      title: 'Add Insurance Coverage',
      riskReduction: 12,
      costImpact: 2.5,
      description: 'Comprehensive coverage reduces financial exposure',
      feasibility: 85,
    },
  ],
  drivers: [
    {
      id: 'driver-1',
      layerName: 'Transport Risk',
      label: 'Port Congestion',
      contributionPct: 18,
      direction: 'increase',
      confidence: 0.85,
      evidence: {
        source: 'port_data_api',
        note: 'Current congestion index at 72% capacity',
      },
    },
  ],
  traces: {
    'Transport Risk': {
      layerName: 'Transport Risk',
      steps: [
        {
          stepId: 'step-1',
          method: 'port_congestion_model',
          summary: 'Calculated congestion risk based on current port capacity',
        },
      ],
    },
  },
};




