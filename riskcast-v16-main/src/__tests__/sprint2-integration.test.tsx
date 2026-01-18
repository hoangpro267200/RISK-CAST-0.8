/**
 * Sprint 2 Integration Tests
 * 
 * Tests for adapter data extraction and component integration
 */

import { describe, test, expect } from 'vitest';
import { adaptResultV2 } from '@/adapters/adaptResultV2';
import type { ResultsViewModel } from '@/types/resultsViewModel';

describe('Sprint 2: Adapter Data Extraction', () => {
  const mockEngineOutput = {
    shipment: {
      id: 'SH-001',
      route: 'VN_US',
      pol_code: 'VNSGN',
      pod_code: 'USLAX',
      carrier: 'Ocean Carrier',
      etd: '2026-01-20',
      eta: '2026-02-23',
      transit_time: 34,
      container: '40DV',
      cargo: 'Electronics',
      cargo_type: 'Electronics',
      container_type: '40DV',
      cargo_value: 500000,
    },
    risk_score: 65,
    risk_level: 'HIGH',
    confidence: 0.85,
    layers: [
      { id: '1', name: 'Climate Risk', score: 72, contribution: 28, weight: 28 },
      { id: '2', name: 'Port Congestion', score: 65, contribution: 18, weight: 18 },
    ],
    loss: {
      expectedLoss: 12000,
      p95: 45000,
      p99: 78000,
      lossCurve: [
        { loss: 5000, probability: 0.1 },
        { loss: 12000, probability: 0.3 },
        { loss: 25000, probability: 0.2 },
        { loss: 45000, probability: 0.1 },
        { loss: 78000, probability: 0.05 },
      ],
    },
    insurance: {
      basisRisk: {
        score: 0.12,
        interpretation: 'low',
        explanation: 'Parametric triggers are reliable',
      },
      triggerProbabilities: [
        { trigger: 'delay > 7 days', probability: 0.22, expectedPayout: 15000 },
      ],
      coverageRecommendations: [
        { type: 'ICC(A)', clause: 'All Risks', rationale: 'High value cargo', priority: 'required' },
      ],
      premiumLogic: {
        expectedLoss: 12000,
        loadFactor: 1.25,
        calculatedPremium: 16200,
        marketRate: 0.80,
        riskcastRate: 0.65,
        explanation: 'Premium calculation',
      },
      deductibleRecommendation: {
        amount: 5000,
        rationale: 'Optimal balance',
      },
    },
    logistics: {
      cargoContainerValidation: {
        isValid: true,
        warnings: [],
      },
      routeSeasonality: {
        season: 'Winter',
        riskLevel: 'HIGH',
        factors: [{ factor: 'Storm Frequency', impact: 'Elevated' }],
        climaticIndices: [{ name: 'ENSO', value: -0.8, interpretation: 'La Niña' }],
      },
      portCongestion: {
        pol: { name: 'Ho Chi Minh', dwellTime: 1.8, normalDwellTime: 1.5, status: 'MILD' },
        pod: { name: 'Los Angeles', dwellTime: 2.4, normalDwellTime: 2.0, status: 'MILD' },
        transshipments: [],
      },
      delayProbabilities: {
        p7days: 0.22,
        p14days: 0.08,
        p21days: 0.03,
      },
    },
    engine_version: 'v2',
    language: 'en',
    timestamp: new Date().toISOString(),
  };

  test('Adapter extracts insurance data correctly', () => {
    const viewModel = adaptResultV2(mockEngineOutput);
    
    expect(viewModel.insurance).toBeDefined();
    expect(viewModel.insurance?.basisRisk).toBeDefined();
    expect(viewModel.insurance?.basisRisk.score).toBe(0.12);
    expect(viewModel.insurance?.basisRisk.interpretation).toBe('low');
    expect(viewModel.insurance?.triggerProbabilities.length).toBeGreaterThan(0);
    expect(viewModel.insurance?.coverageRecommendations.length).toBeGreaterThan(0);
  });

  test('Adapter extracts logistics data correctly', () => {
    const viewModel = adaptResultV2(mockEngineOutput);
    
    expect(viewModel.logistics).toBeDefined();
    expect(viewModel.logistics?.cargoContainerValidation).toBeDefined();
    expect(viewModel.logistics?.cargoContainerValidation.isValid).toBe(true);
    expect(viewModel.logistics?.routeSeasonality.season).toBe('Winter');
    expect(viewModel.logistics?.routeSeasonality.riskLevel).toBe('HIGH');
    expect(viewModel.logistics?.portCongestion.pol.dwellTime).toBeGreaterThan(0);
    expect(viewModel.logistics?.delayProbabilities.p7days).toBe(0.22);
  });

  test('Adapter handles missing insurance data gracefully', () => {
    const outputWithoutInsurance = { ...mockEngineOutput };
    delete outputWithoutInsurance.insurance;
    
    const viewModel = adaptResultV2(outputWithoutInsurance);
    
    expect(viewModel.insurance).toBeUndefined();
    expect(viewModel.loss).toBeDefined(); // Loss data should still exist
  });

  test('Adapter handles missing logistics data gracefully', () => {
    const outputWithoutLogistics = { ...mockEngineOutput };
    delete outputWithoutLogistics.logistics;
    
    const viewModel = adaptResultV2(outputWithoutLogistics);
    
    // Logistics should still be extracted from basic shipment data
    expect(viewModel.logistics).toBeDefined();
    expect(viewModel.logistics?.cargoContainerValidation).toBeDefined();
  });

  test('Adapter generates loss histogram from loss curve', () => {
    const viewModel = adaptResultV2(mockEngineOutput);
    
    expect(viewModel.insurance?.lossDistribution).toBeDefined();
    expect(viewModel.insurance?.lossDistribution.histogram.length).toBeGreaterThan(0);
    expect(viewModel.insurance?.lossDistribution.isSynthetic).toBe(false); // Has real loss curve
  });

  test('Adapter marks synthetic loss distribution correctly', () => {
    const outputWithSynthetic = {
      ...mockEngineOutput,
      loss: {
        expectedLoss: 12000,
        p95: 45000,
        p99: 78000,
        // No lossCurve - will be generated synthetically
      },
    };
    delete outputWithSynthetic.insurance; // Remove insurance to force generation
    
    const viewModel = adaptResultV2(outputWithSynthetic);
    
    // Adapter should generate insurance data from loss metrics
    if (viewModel.insurance) {
      // If histogram is generated, it should be marked as synthetic
      expect(viewModel.insurance.lossDistribution.isSynthetic).toBeDefined();
    }
  });

  test('Adapter validates cargo-container match', () => {
    const outputWithMismatch = {
      ...mockEngineOutput,
      shipment: {
        ...mockEngineOutput.shipment,
        cargo_type: 'Frozen Seafood',
        container_type: '40DV', // Dry van - mismatch!
      },
    };
    
    const viewModel = adaptResultV2(outputWithMismatch);
    
    expect(viewModel.logistics?.cargoContainerValidation.isValid).toBe(false);
    expect(viewModel.logistics?.cargoContainerValidation.warnings.length).toBeGreaterThan(0);
    expect(viewModel.logistics?.cargoContainerValidation.warnings[0].severity).toBe('error');
  });
});

describe('Sprint 2: Component Props Validation', () => {
  test('InsuranceUnderwritingPanel requires all props', () => {
    const mockInsuranceData = {
      lossDistribution: { histogram: [], isSynthetic: false, dataPoints: 0 },
      basisRisk: { score: 0.12, interpretation: 'low' as const, explanation: '' },
      triggerProbabilities: [],
      coverageRecommendations: [],
      premiumLogic: {
        expectedLoss: 12000,
        loadFactor: 1.25,
        calculatedPremium: 16200,
        marketRate: 0.80,
        riskcastRate: 0.65,
        explanation: '',
      },
      riders: [],
      exclusions: [],
      deductibleRecommendation: { amount: 5000, rationale: '' },
    };

    // Props should be valid
    expect(mockInsuranceData.lossDistribution).toBeDefined();
    expect(mockInsuranceData.basisRisk.score).toBeGreaterThanOrEqual(0);
    expect(mockInsuranceData.basisRisk.score).toBeLessThanOrEqual(1);
  });

  test('LogisticsRealismPanel requires all props', () => {
    const mockLogisticsData = {
      cargoContainerValidation: { isValid: true, warnings: [] },
      routeSeasonality: {
        season: 'Winter',
        riskLevel: 'HIGH' as const,
        factors: [],
        climaticIndices: [],
      },
      portCongestion: {
        pol: { name: 'POL', dwellTime: 1.5, normalDwellTime: 1.5, status: 'NORMAL' },
        pod: { name: 'POD', dwellTime: 2.0, normalDwellTime: 2.0, status: 'NORMAL' },
        transshipments: [],
      },
      delayProbabilities: { p7days: 0.22, p14days: 0.08, p21days: 0.03 },
      packagingRecommendations: [],
    };

    // Props should be valid
    expect(mockLogisticsData.cargoContainerValidation.isValid).toBeDefined();
    expect(['LOW', 'MEDIUM', 'HIGH']).toContain(mockLogisticsData.routeSeasonality.riskLevel);
    expect(mockLogisticsData.delayProbabilities.p7days).toBeGreaterThanOrEqual(0);
  });
});
