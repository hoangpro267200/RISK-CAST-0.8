import React from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { RiskAnalysisResult } from '../types';

export type RenderWithProvidersOptions = Omit<RenderOptions, 'wrapper'> & {
  wrapper?: React.ComponentType<React.PropsWithChildren>;
  userEventOptions?: Parameters<typeof userEvent.setup>[0];
};

export function renderWithProviders(ui: React.ReactElement, options: RenderWithProvidersOptions = {}) {
  const { wrapper: CustomWrapper, userEventOptions, ...renderOptions } = options;
  const user = userEvent.setup(userEventOptions);

  const Wrapper: React.FC<React.PropsWithChildren> = ({ children }) => {
    const content = <React.StrictMode>{children}</React.StrictMode>;
    return CustomWrapper ? <CustomWrapper>{content}</CustomWrapper> : content;
  };

  return {
    user,
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
  };
}

export function createMockRiskData(overrides: Partial<RiskAnalysisResult> = {}): RiskAnalysisResult {
  const base: RiskAnalysisResult = {
    shipment: {
      shipmentId: 'SHP-0001',
      route: { pol: 'SGSIN', pod: 'USLAX' },
      carrier: 'MAERSK',
      etd: '2025-01-01',
      eta: '2025-01-20',
      incoterm: 'FOB',
      cargoValue: 1_250_000,
      dataConfidence: 0.62,
      lastUpdated: '2025-01-01T00:00:00Z',
    },
    riskScore: {
      overallScore: 72,
      riskLevel: 'HIGH',
      verdict: 'High risk — review mitigation options.',
      dataConfidence: 0.68,
      confidenceLower: 0.55,
      confidenceUpper: 0.78,
      engineVersion: 'engine-1.0.0',
    },
    layers: [
      {
        name: 'Geopolitical Risk',
        score: 85,
        contribution: 40,
        status: 'ALERT',
        notes: 'Elevated sanctions exposure and conflict risk.',
        confidence: 75,
      },
      {
        name: 'Port Congestion',
        score: 62,
        contribution: 35,
        status: 'WARNING',
        notes: 'Congestion rising at key transshipment hub.',
        confidence: 65,
      },
      {
        name: 'Weather Risk',
        score: 28,
        contribution: 25,
        status: 'OK',
        notes: 'No major disruptions expected in the next 7 days.',
        confidence: 82,
      },
    ],
    decisionSignal: {
      recommendation: 'BUY',
      rationale: 'Insurance is recommended given high tail risk and uncertain geopolitics.',
      providers: [
        { name: 'Provider A', premium: 12000, fitScore: 0.78 },
        { name: 'Provider B', premium: 9800, fitScore: 0.71 },
      ],
    },
    timing: {
      optimalWindow: '2025-01-03 → 2025-01-06',
      riskReduction: 6,
    },
    scenarios: [
      {
        title: 'Reroute via alternate hub',
        riskReduction: 12,
        costImpact: 4.5,
        description: 'Switch transshipment to reduce geopolitics exposure.',
        feasibility: 70,
      },
      {
        title: 'Delay departure 48h',
        riskReduction: 5,
        costImpact: 1.2,
        description: 'Avoid peak congestion window.',
        feasibility: 85,
      },
    ],
    financial: null,
    aiNarrative: {
      executiveSummary: 'Overall risk is high due to geopolitical uncertainty.',
      keyInsights: ['Sanctions exposure is elevated', 'Port congestion trending upward'],
      actionItems: ['Consider coverage', 'Review reroute scenarios'],
      riskDrivers: ['Sanctions', 'Conflict', 'Congestion'],
      confidenceNotes: 'Confidence moderate; some data sources are stale.',
    },
    timeline: [
      {
        phase: 'Pre-carriage',
        status: 'completed',
        riskLevel: 'LOW',
        events: [{ time: 'T-7d', description: 'Booking confirmed' }],
      },
      {
        phase: 'Main carriage',
        status: 'current',
        riskLevel: 'HIGH',
        events: [{ time: 'T+0', description: 'Departed POL' }],
      },
    ],
    riskOverTime: [
      { date: '2025-01-01', risk: 68, phase: 'Pre-carriage' },
      { date: '2025-01-05', risk: 72, phase: 'Main carriage' },
      { date: '2025-01-10', risk: 70, phase: 'Main carriage' },
    ],
    riskScenarioProjections: [
      { date: '2025-01-01', p10: 55, p50: 70, p90: 88, expected: 74 },
      { date: '2025-01-07', p10: 50, p50: 72, p90: 92, expected: 76 },
      { date: '2025-01-14', p10: 45, p50: 68, p90: 90, expected: 72 },
    ],
    dataReliability: [
      { domain: 'Geopolitics', confidence: 0.7, completeness: 0.8, freshness: 0.6, notes: 'Some feeds delayed.' },
      { domain: 'Ports', confidence: 0.75, completeness: 0.9, freshness: 0.7, notes: 'Near real-time AIS.' },
    ],
    drivers: [
      {
        id: 'drv-geo-1',
        layerName: 'Geopolitical Risk',
        label: 'Sanctions exposure',
        contributionPct: 55,
        direction: 'increase',
        confidence: 0.85,
        evidence: { source: 'external', note: 'Recent sanctions update increased risk band.' },
      },
      {
        id: 'drv-geo-2',
        layerName: 'Geopolitical Risk',
        label: 'Conflict escalation',
        contributionPct: 45,
        direction: 'increase',
        confidence: 0.78,
        evidence: { source: 'external', note: 'Conflict proximity raises disruption probability.' },
      },
      {
        id: 'drv-port-1',
        layerName: 'Port Congestion',
        label: 'Queue length trend',
        contributionPct: 60,
        direction: 'increase',
        confidence: 0.72,
        evidence: { source: 'model', note: 'Port congestion model predicts longer dwell time.' },
      },
    ],
    traces: {
      'Geopolitical Risk': {
        layerName: 'Geopolitical Risk',
        steps: [
          { stepId: 'geo-1', method: 'geo_risk_lookup', summary: 'Lookup regional geopolitics risk index.' },
          { stepId: 'geo-2', method: 'aggregation', summary: 'Aggregate signals into layer score.' },
        ],
      },
      'Port Congestion': {
        layerName: 'Port Congestion',
        steps: [{ stepId: 'port-1', method: 'port_congestion_model', summary: 'Predict dwell/queue times.' }],
        sensitivity: [{ name: 'Dwell time', impact: 4.2 }],
      },
    },
  };

  return {
    ...base,
    ...overrides,
    shipment: { ...base.shipment, ...(overrides.shipment ?? {}) },
    riskScore: { ...base.riskScore, ...(overrides.riskScore ?? {}) },
    layers: overrides.layers ?? base.layers,
    decisionSignal: overrides.decisionSignal ?? base.decisionSignal,
    timing: overrides.timing ?? base.timing,
    scenarios: overrides.scenarios ?? base.scenarios,
    financial: overrides.financial ?? base.financial,
    aiNarrative: overrides.aiNarrative ?? base.aiNarrative,
    timeline: overrides.timeline ?? base.timeline,
    riskOverTime: overrides.riskOverTime ?? base.riskOverTime,
    riskScenarioProjections: overrides.riskScenarioProjections ?? base.riskScenarioProjections,
    dataReliability: overrides.dataReliability ?? base.dataReliability,
    drivers: overrides.drivers ?? base.drivers,
    traces: overrides.traces ?? base.traces,
  };
}

