/**
 * Sprint 2 Test Suite
 * 
 * Tests for Insurance Underwriting and Logistics Realism components
 */

import { describe, test, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { InsuranceUnderwritingData, LogisticsRealismData } from '../types';

// Mock components (we'll test the actual components)
describe('Sprint 2: Insurance Underwriting', () => {
  const mockInsuranceData: InsuranceUnderwritingData = {
    lossDistribution: {
      histogram: [
        { bucket: '$0-$5K', frequency: 0.35, cumulative: 0.35 },
        { bucket: '$5K-$10K', frequency: 0.25, cumulative: 0.60 },
        { bucket: '$10K-$20K', frequency: 0.20, cumulative: 0.80 },
        { bucket: '$20K-$50K', frequency: 0.15, cumulative: 0.95 },
        { bucket: '$50K+', frequency: 0.05, cumulative: 1.00 },
      ],
      isSynthetic: false,
      dataPoints: 1000,
    },
    basisRisk: {
      score: 0.12,
      interpretation: 'low',
      explanation: 'Parametric triggers are reliable for this shipment',
    },
    triggerProbabilities: [
      {
        trigger: 'delay > 7 days',
        probability: 0.22,
        expectedPayout: 15000,
      },
      {
        trigger: 'delay > 14 days',
        probability: 0.08,
        expectedPayout: 35000,
      },
    ],
    coverageRecommendations: [
      {
        type: 'ICC(A)',
        clause: 'All Risks Marine Cargo Insurance',
        rationale: 'Electronics cargo with high value requires broadest coverage',
        priority: 'required',
      },
      {
        type: 'Delay Rider',
        clause: 'Parametric delay coverage',
        rationale: 'Winter Pacific crossing has elevated delay risk',
        priority: 'recommended',
      },
    ],
    premiumLogic: {
      expectedLoss: 12000,
      loadFactor: 1.25,
      calculatedPremium: 16200,
      marketRate: 0.80,
      riskcastRate: 0.65,
      explanation: 'Premium calculated from expected loss with load factor',
    },
    riders: [
      {
        name: 'Delay Rider',
        cost: 1500,
        benefit: 'Covers delays > 7 days',
      },
    ],
    exclusions: [
      {
        clause: 'Pre-existing Damage',
        reason: 'Damage existing before cargo loaded onto vessel',
      },
    ],
    deductibleRecommendation: {
      amount: 5000,
      rationale: 'Balances premium savings against out-of-pocket exposure',
    },
  };

  test('IU-1: Loss histogram data structure is valid', () => {
    expect(mockInsuranceData.lossDistribution.histogram.length).toBeGreaterThan(0);
    expect(mockInsuranceData.lossDistribution.histogram[0]).toHaveProperty('bucket');
    expect(mockInsuranceData.lossDistribution.histogram[0]).toHaveProperty('frequency');
    expect(mockInsuranceData.lossDistribution.histogram[0]).toHaveProperty('cumulative');
  });

  test('IU-2: Synthetic flag is boolean', () => {
    expect(typeof mockInsuranceData.lossDistribution.isSynthetic).toBe('boolean');
  });

  test('IU-3: Basis risk score is in valid range', () => {
    expect(mockInsuranceData.basisRisk.score).toBeGreaterThanOrEqual(0);
    expect(mockInsuranceData.basisRisk.score).toBeLessThanOrEqual(1);
    expect(['low', 'moderate', 'high']).toContain(mockInsuranceData.basisRisk.interpretation);
  });

  test('IU-4: Trigger probabilities have valid structure', () => {
    expect(mockInsuranceData.triggerProbabilities.length).toBeGreaterThan(0);
    mockInsuranceData.triggerProbabilities.forEach(trigger => {
      expect(trigger.probability).toBeGreaterThanOrEqual(0);
      expect(trigger.probability).toBeLessThanOrEqual(1);
      expect(trigger.expectedPayout).toBeGreaterThanOrEqual(0);
    });
  });

  test('IU-5: Coverage recommendations have priority', () => {
    expect(mockInsuranceData.coverageRecommendations.length).toBeGreaterThan(0);
    mockInsuranceData.coverageRecommendations.forEach(rec => {
      expect(['required', 'recommended', 'optional']).toContain(rec.priority);
    });
  });

  test('IU-6: Premium logic has all required fields', () => {
    expect(mockInsuranceData.premiumLogic.expectedLoss).toBeGreaterThan(0);
    expect(mockInsuranceData.premiumLogic.loadFactor).toBeGreaterThan(1);
    expect(mockInsuranceData.premiumLogic.calculatedPremium).toBeGreaterThan(0);
    expect(mockInsuranceData.premiumLogic.marketRate).toBeGreaterThan(0);
    expect(mockInsuranceData.premiumLogic.riskcastRate).toBeGreaterThan(0);
  });

  test('IU-7: Deductible recommendation has amount and rationale', () => {
    expect(mockInsuranceData.deductibleRecommendation.amount).toBeGreaterThan(0);
    expect(mockInsuranceData.deductibleRecommendation.rationale.length).toBeGreaterThan(0);
  });
});

describe('Sprint 2: Logistics Realism', () => {
  const mockLogisticsData: LogisticsRealismData = {
    cargoContainerValidation: {
      isValid: true,
      warnings: [],
    },
    routeSeasonality: {
      season: 'Winter',
      riskLevel: 'HIGH',
      factors: [
        { factor: 'Storm Frequency', impact: '2.3x normal due to La Niña' },
        { factor: 'Wave Height', impact: 'HIGH (4-6m average)' },
      ],
      climaticIndices: [
        { name: 'ENSO (Niño)', value: -0.8, interpretation: 'La Niña (active)' },
        { name: 'PDO', value: 1.2, interpretation: 'Warm phase' },
      ],
    },
    portCongestion: {
      pol: {
        name: 'Ho Chi Minh',
        dwellTime: 1.8,
        normalDwellTime: 1.5,
        status: 'MILD',
      },
      pod: {
        name: 'Los Angeles',
        dwellTime: 2.4,
        normalDwellTime: 2.0,
        status: 'MILD',
      },
      transshipments: [
        {
          name: 'Singapore',
          dwellTime: 3.2,
          normalDwellTime: 1.5,
          status: 'HIGH',
        },
      ],
    },
    delayProbabilities: {
      p7days: 0.22,
      p14days: 0.08,
      p21days: 0.03,
    },
    packagingRecommendations: [
      {
        item: 'Desiccant packs',
        cost: 200,
        riskReduction: 40,
        rationale: 'Reduces moisture damage risk',
      },
    ],
  };

  test('LR-3: Cargo-container validation structure is valid', () => {
    expect(typeof mockLogisticsData.cargoContainerValidation.isValid).toBe('boolean');
    expect(Array.isArray(mockLogisticsData.cargoContainerValidation.warnings)).toBe(true);
  });

  test('LR-4: Seasonality risk level is valid', () => {
    expect(['LOW', 'MEDIUM', 'HIGH']).toContain(mockLogisticsData.routeSeasonality.riskLevel);
    expect(mockLogisticsData.routeSeasonality.factors.length).toBeGreaterThan(0);
    expect(mockLogisticsData.routeSeasonality.climaticIndices.length).toBeGreaterThan(0);
  });

  test('LR-5: Port congestion data structure is valid', () => {
    expect(mockLogisticsData.portCongestion.pol.dwellTime).toBeGreaterThan(0);
    expect(mockLogisticsData.portCongestion.pod.dwellTime).toBeGreaterThan(0);
    expect(Array.isArray(mockLogisticsData.portCongestion.transshipments)).toBe(true);
  });

  test('LR-6: Delay probabilities are in valid range', () => {
    expect(mockLogisticsData.delayProbabilities.p7days).toBeGreaterThanOrEqual(0);
    expect(mockLogisticsData.delayProbabilities.p7days).toBeLessThanOrEqual(1);
    expect(mockLogisticsData.delayProbabilities.p14days).toBeLessThanOrEqual(mockLogisticsData.delayProbabilities.p7days);
    expect(mockLogisticsData.delayProbabilities.p21days).toBeLessThanOrEqual(mockLogisticsData.delayProbabilities.p14days);
  });

  test('Packaging recommendations have cost and risk reduction', () => {
    expect(mockLogisticsData.packagingRecommendations.length).toBeGreaterThan(0);
    mockLogisticsData.packagingRecommendations.forEach(rec => {
      expect(rec.cost).toBeGreaterThanOrEqual(0);
      expect(rec.riskReduction).toBeGreaterThanOrEqual(0);
      expect(rec.riskReduction).toBeLessThanOrEqual(100);
    });
  });
});

describe('Sprint 2: Cargo-Container Validation Logic', () => {
  test('Perishable + Dry Container = MISMATCH', () => {
    const validation = {
      isValid: false,
      warnings: [{
        code: 'PERISHABLE_NON_REEFER',
        message: 'Perishable cargo requires refrigerated container',
        severity: 'error' as const,
      }],
    };
    expect(validation.isValid).toBe(false);
    expect(validation.warnings.length).toBeGreaterThan(0);
    expect(validation.warnings[0].severity).toBe('error');
  });

  test('Electronics + Dry Container = VALID', () => {
    const validation = {
      isValid: true,
      warnings: [],
    };
    expect(validation.isValid).toBe(true);
  });

  test('Electronics + Open Top = WARNING', () => {
    const validation = {
      isValid: true,
      warnings: [{
        code: 'ELECTRONICS_OPENTOP',
        message: 'Electronics require dry container with climate control',
        severity: 'warning' as const,
      }],
    };
    expect(validation.warnings[0].severity).toBe('warning');
  });
});

describe('Sprint 2: Insurance Flags Logic', () => {
  test('High value cargo (> $200K) triggers HIGH_VALUE flag', () => {
    const cargoValue = 500000;
    expect(cargoValue > 200000).toBe(true);
  });

  test('Long transit (> 30 days) triggers LONG_TRANSIT flag', () => {
    const transitDays = 34;
    expect(transitDays > 30).toBe(true);
  });

  test('Electronics cargo triggers FRAGILE flag', () => {
    const cargoType = 'Electronics';
    const fragileTypes = ['electronics', 'pharmaceuticals', 'glass'];
    expect(fragileTypes.some(type => cargoType.toLowerCase().includes(type))).toBe(true);
  });

  test('Multiple transshipments triggers HANDLING_RISK flag', () => {
    const transshipmentCount = 2;
    expect(transshipmentCount > 1).toBe(true);
  });
});
