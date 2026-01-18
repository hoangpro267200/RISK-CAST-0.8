/**
 * Sprint 1 Test Suite
 * 
 * Tests for Algorithm Explainability and Personalized Narrative
 */

import { describe, test, expect } from 'vitest';
import { generateNarrativeViewModel } from '@/services/narrativeGenerator';
import type { ResultsViewModel } from '@/types/resultsViewModel';

describe('Sprint 1: Narrative Personalization', () => {
  const mockViewModel: ResultsViewModel = {
    overview: {
      shipment: {
        id: 'SH-001',
        route: 'VN_US',
        pol: { code: 'VNSGN', name: 'Ho Chi Minh' },
        pod: { code: 'USLAX', name: 'Los Angeles' },
        carrier: 'Ocean Carrier',
        etd: '2026-01-20',
        eta: '2026-02-23',
        transitTime: 34,
        container: '40DV',
        cargo: 'Electronics',
        cargoType: 'Electronics',
        containerType: '40DV',
        incoterm: 'FOB',
        cargoValue: 500000,
      },
      riskScore: {
        score: 65,
        level: 'HIGH',
        confidence: 85,
        confidenceSource: 'Based on 12 data points',
      },
      profile: {
        score: 65,
        level: 'HIGH',
        confidence: 85,
        explanation: [],
        factors: {},
        matrix: {
          probability: 6,
          severity: 7,
          quadrant: 'High-High',
          description: 'High risk profile',
        },
      },
      reasoning: {
        explanation: 'High risk due to climate and port congestion',
      },
    },
    breakdown: {
      layers: [
        { 
          id: '1', 
          name: 'Climate Risk', 
          score: 72, 
          contribution: 28,
          category: 'EXTERNAL',
        },
        { 
          id: '2', 
          name: 'Port Congestion', 
          score: 65, 
          contribution: 18,
          category: 'EXTERNAL',
        },
        { 
          id: '3', 
          name: 'Cargo Sensitivity', 
          score: 58, 
          contribution: 15,
          category: 'CARGO',
        },
      ],
      factors: {},
    },
    timeline: {
      projections: [],
      hasData: false,
    },
    decisions: {
      insurance: {
        status: 'RECOMMENDED',
        recommendation: 'BUY',
        rationale: 'High value cargo requires coverage',
        riskDeltaPoints: -10,
        costImpactUsd: 1500,
        providers: [],
      },
      timing: {
        status: 'OPTIONAL',
        recommendation: 'KEEP_ETD',
        rationale: 'Current timing acceptable',
        optimalWindow: null,
        riskReductionPoints: null,
        costImpactUsd: null,
      },
      routing: {
        status: 'NOT_NEEDED',
        recommendation: 'KEEP_ROUTE',
        rationale: 'Route is optimal',
        bestAlternative: null,
        tradeoff: null,
        riskReductionPoints: null,
        costImpactUsd: null,
      },
    },
    loss: {
      p95: 45000,
      p99: 78000,
      expectedLoss: 12000,
      tailContribution: 15,
    },
    scenarios: [],
    drivers: [
      { name: 'Climate Risk', impact: 28, description: 'Pacific winter storms' },
      { name: 'Port Congestion', impact: 18, description: 'Singapore delays' },
      { name: 'Cargo Sensitivity', impact: 15, description: 'Electronics moisture risk' },
    ],
    meta: {
      warnings: [],
      source: {
        canonicalRiskScoreFrom: 'profile.score',
        canonicalDriversFrom: 'drivers',
      },
      engineVersion: 'v2',
      language: 'en',
      timestamp: new Date().toISOString(),
      dataFreshness: 'fresh',
      dataQuality: 'real',
    },
  };

  test('NP-1: Narrative contains cargo type', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    expect(narrative.personalizedSummary).toContain('ELECTRONICS');
    expect(narrative.personalizedSummary).toContain('Electronics');
  });

  test('NP-2: Narrative contains route', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    expect(narrative.personalizedSummary).toContain('Ho Chi Minh');
    expect(narrative.personalizedSummary).toContain('Los Angeles');
  });

  test('NP-3: Narrative contains top 3 drivers', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    expect(narrative.topRiskFactors.length).toBeGreaterThanOrEqual(3);
    expect(narrative.topRiskFactors[0].factor).toBe('Climate Risk');
    expect(narrative.topRiskFactors[1].factor).toBe('Port Congestion');
  });

  test('NP-4: Actions have cost/benefit', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    // Check that action items exist
    expect(narrative.actionItems.length).toBeGreaterThan(0);
  });

  test('NP-5: Loss expectations included', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    expect(narrative.personalizedSummary).toContain('$12K'); // expectedLoss
    expect(narrative.personalizedSummary).toContain('$45K'); // p95
    expect(narrative.personalizedSummary).toContain('$78K'); // p99
  });

  test('NP-6: No generic phrases', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    expect(narrative.personalizedSummary).not.toContain('moderate risk');
    expect(narrative.personalizedSummary).not.toContain('consider insurance');
    expect(narrative.personalizedSummary).not.toContain('your shipment has');
  });

  test('Narrative includes carrier name', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    expect(narrative.personalizedSummary).toContain('Ocean Carrier');
  });

  test('Narrative includes transit time', () => {
    const narrative = generateNarrativeViewModel(mockViewModel);
    expect(narrative.personalizedSummary).toContain('34');
    expect(narrative.personalizedSummary).toContain('day');
  });
});

describe('Sprint 1: Algorithm Data Structure', () => {
  test('Algorithm types are properly exported', async () => {
    const algorithmTypes = await import('@/types/algorithmTypes');
    expect(algorithmTypes).toHaveProperty('FAHPData');
    expect(algorithmTypes).toHaveProperty('TOPSISData');
    expect(algorithmTypes).toHaveProperty('MonteCarloData');
  });

  test('Insurance types are properly exported', async () => {
    const insuranceTypes = await import('@/types/insuranceTypes');
    expect(insuranceTypes).toHaveProperty('InsuranceUnderwritingData');
  });

  test('Logistics types are properly exported', async () => {
    const logisticsTypes = await import('@/types/logisticsTypes');
    expect(logisticsTypes).toHaveProperty('LogisticsRealismData');
  });
});
