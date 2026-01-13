/**
 * Unit tests for adaptResultV2 adapter function
 * 
 * Tests cover:
 * - Canonical happy path with all fields present
 * - Redundancy handling (precedence rules)
 * - Missing arrays and fields
 * - Invalid types and coercion
 * - Timeline ordering violations
 * - Invalid dates
 */

import { describe, it, expect } from 'vitest';
import { adaptResultV2 } from './adaptResultV2';
import type { EngineCompleteResultV2 } from '@/types/engine';

describe('adaptResultV2', () => {
  // ============================================================
  // TEST A: Canonical happy path with all fields present
  // ============================================================
  describe('A) Canonical happy path', () => {
    it('should normalize complete engine result correctly', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-SGN-LAX-1234567890',
          route: 'SGN → LAX',
          pol_code: 'SGN',
          pod_code: 'LAX',
          carrier: 'CMA CGM',
          etd: '2024-01-15',
          eta: '2024-02-05',
          transit_time: 21,
          container: '40HC',
          cargo: 'Electronics',
          incoterm: 'FOB',
          cargo_value: 50000,
        },
        risk_score: 75.5,
        risk_level: 'High',
        confidence: 0.85,
        profile: {
          score: 75.5,
          level: 'High',
          confidence: 0.85,
          explanation: ['Risk score indicates high risk', 'Primary drivers identified'],
          factors: {
            delay: 0.7,
            port: 0.6,
            climate: 0.5,
          },
          matrix: {
            probability: 7,
            severity: 8,
            quadrant: 'High-High',
            description: 'High probability, high severity',
          },
        },
        drivers: [
          { name: 'Climate Risk', impact: 0.85, description: 'Storm probability elevated' },
          { name: 'Port Congestion', impact: 0.6, description: 'High port congestion' },
        ],
        layers: [
          { name: 'Transport', score: 75.6, contribution: 0.756 },
          { name: 'Weather', score: 62.3, contribution: 0.623 },
        ],
        riskScenarioProjections: [
          { date: '2024-01-15', p10: 64.2, p50: 75.5, p90: 86.8, phase: 'Booking' },
          { date: '2024-01-20', p10: 68.0, p50: 78.0, p90: 88.0, phase: 'Ocean Transit' },
        ],
        loss: {
          p95: 22500,
          p99: 27000,
          expectedLoss: 15000,
          tailContribution: 28.5,
        },
        scenarios: [
          {
            id: 'insurance',
            title: 'Add Cargo Insurance',
            category: 'INSURANCE',
            riskReduction: 26.4,
            costImpact: 750,
            isRecommended: true,
            rank: 1,
            description: 'Comprehensive cargo insurance',
          },
        ],
        decision_summary: {
          insurance: {
            status: 'RECOMMENDED',
            recommendation: 'BUY',
            rationale: 'High risk level warrants insurance',
            risk_delta_points: 26.4,
            cost_impact_usd: 750,
            providers: [],
          },
          timing: {
            status: 'OPTIONAL',
            recommendation: 'KEEP_ETD',
            rationale: 'Current timing acceptable',
            optimal_window: { start: '2024-01-18', end: '2024-01-22' },
            risk_reduction_points: null,
            cost_impact_usd: null,
          },
          routing: {
            status: 'OPTIONAL',
            recommendation: 'KEEP_ROUTE',
            rationale: 'Current route acceptable',
            best_alternative: null,
            tradeoff: null,
            risk_reduction_points: null,
            cost_impact_usd: null,
          },
        },
        engine_version: 'v2',
        language: 'vi',
        timestamp: '2024-01-15T10:30:00Z',
      };

      const result = adaptResultV2(input);

      // Verify structure
      expect(result).toHaveProperty('shipment');
      expect(result).toHaveProperty('riskScore');
      expect(result).toHaveProperty('profile');
      expect(result).toHaveProperty('drivers');
      expect(result).toHaveProperty('layers');
      expect(result).toHaveProperty('timeline');
      expect(result).toHaveProperty('loss');
      expect(result).toHaveProperty('scenarios');
      expect(result).toHaveProperty('decisions');
      expect(result).toHaveProperty('meta');

      // Verify risk score (from profile.score)
      expect(result.overview.riskScore.score).toBe(75.5);
      expect(result.overview.riskScore.level).toBe('High');
      expect(result.overview.riskScore.confidence).toBe(85); // 0.85 -> 85%

      // Verify meta source tracking
      expect(result.meta.source.canonicalRiskScoreFrom).toBe('profile.score');
      expect(result.meta.source.canonicalDriversFrom).toBe('drivers');

      // Verify drivers normalized
      expect(result.drivers).toHaveLength(2);
      expect(result.drivers[0]?.impact).toBe(85); // 0.85 -> 85%
      expect(result.drivers[0]?.name).toBe('Climate Risk');

      // Verify timeline
      expect(result.timeline.hasData).toBe(true);
      expect(result.timeline.projections).toHaveLength(2);
      const firstProj = result.timeline.projections[0];
      if (firstProj) {
        expect(firstProj.p10).toBeLessThanOrEqual(firstProj.p50);
        expect(firstProj.p50).toBeLessThanOrEqual(firstProj.p90);
      }

      // Verify loss
      expect(result.loss).not.toBeNull();
      expect(result.loss?.expectedLoss).toBe(15000);

      // Verify scenarios
      expect(result.scenarios).toHaveLength(1);
      expect(result.scenarios[0]?.id).toBe('insurance');
      expect(result.scenarios[0]?.riskReduction).toBe(26.4);

      // Verify no warnings for complete data
      expect(result.meta.warnings).toHaveLength(0);
    });
  });

  // ============================================================
  // TEST B: Redundancy path - only overall_risk exists
  // ============================================================
  describe('B) Redundancy handling', () => {
    it('should use overall_risk when profile.score and risk_score are missing', () => {
      const input: EngineCompleteResultV2 = {
        overall_risk: 65.5,
        risk_level: 'Medium',
        confidence: 0.7,
        shipment: {
          id: 'SH-TEST',
          route: 'TEST → TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.score).toBe(65.5);
      expect(result.meta.source.canonicalRiskScoreFrom).toBe('overall_risk');
      expect(result.meta.warnings).toContain('Risk score missing - using default 0');
    });

    it('should prefer profile.score over risk_score', () => {
      const input: EngineCompleteResultV2 = {
        risk_score: 70,
        profile: {
          score: 75.5,
        },
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.score).toBe(75.5);
      expect(result.meta.source.canonicalRiskScoreFrom).toBe('profile.score');
    });

    it('should prefer risk_score over overall_risk', () => {
      const input: EngineCompleteResultV2 = {
        risk_score: 70,
        overall_risk: 65,
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.score).toBe(70);
      expect(result.meta.source.canonicalRiskScoreFrom).toBe('risk_score');
    });

    it('should use risk_factors when drivers is missing', () => {
      const input: EngineCompleteResultV2 = {
        risk_factors: [
          { name: 'Test Driver', impact: 0.5, description: 'Test' },
        ],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.drivers).toHaveLength(1);
      expect(result.meta.source.canonicalDriversFrom).toBe('risk_factors');
    });

    it('should use factors when drivers and risk_factors are missing', () => {
      const input: EngineCompleteResultV2 = {
        factors: [
          { name: 'Test Driver', impact: 0.5, description: 'Test' },
        ],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.drivers).toHaveLength(1);
      expect(result.meta.source.canonicalDriversFrom).toBe('factors');
    });
  });

  // ============================================================
  // TEST C: Missing arrays and fields
  // ============================================================
  describe('C) Missing arrays and fields', () => {
    it('should handle empty drivers array', () => {
      const input: EngineCompleteResultV2 = {
        drivers: [],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.drivers).toHaveLength(0);
      expect(result.meta.source.canonicalDriversFrom).toBe('empty');
    });

    it('should handle missing scenarios', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.scenarios).toHaveLength(0);
    });

    it('should handle missing riskScenarioProjections', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.timeline.projections).toHaveLength(0);
      expect(result.timeline.hasData).toBe(false);
    });

    it('should handle missing loss', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.loss).toBeNull();
    });

    it('should handle minimal input with defaults', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.score).toBe(0);
      expect(result.overview.riskScore.level).toBe('Unknown');
      expect(result.drivers).toHaveLength(0);
      expect(result.breakdown.layers).toHaveLength(0);
      expect(result.scenarios).toHaveLength(0);
    });
  });

  // ============================================================
  // TEST D: Invalid types and coercion
  // ============================================================
  describe('D) Invalid types and coercion', () => {
    it('should coerce string confidence to number', () => {
      const input: EngineCompleteResultV2 = {
        confidence: '0.8',
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.confidence).toBe(80); // "0.8" -> 0.8 -> 80%
    });

    it('should coerce string risk_score to number', () => {
      const input: EngineCompleteResultV2 = {
        risk_score: '75.5',
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.score).toBe(75.5);
    });

    it('should coerce string factors values to numbers', () => {
      const input: EngineCompleteResultV2 = {
        profile: {
          factors: {
            delay: '0.7',
            port: '0.6',
          },
        },
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.breakdown.factors.delay).toBe(70); // "0.7" -> 0.7 -> 70%
      expect(result.breakdown.factors.port).toBe(60);
    });

    it('should handle null values safely', () => {
      const input: EngineCompleteResultV2 = {
        risk_score: null,
        confidence: null,
        drivers: null,
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.score).toBe(0);
      expect(result.overview.riskScore.confidence).toBe(0);
      expect(result.drivers).toHaveLength(0);
    });

    it('should handle undefined values safely', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      // Should not throw and return valid model
      expect(result).toBeDefined();
      expect(result.overview.riskScore.score).toBe(0);
    });
  });

  // ============================================================
  // TEST E: Timeline ordering violation
  // ============================================================
  describe('E) Timeline ordering violation', () => {
    it('should repair p10 > p50 ordering violation', () => {
      const input: EngineCompleteResultV2 = {
        riskScenarioProjections: [
          { date: '2024-01-15', p10: 80, p50: 70, p90: 90, phase: 'Test' },
        ],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      const firstProj = result.timeline.projections[0];
      if (firstProj) {
        expect(firstProj.p10).toBeLessThanOrEqual(firstProj.p50);
        expect(firstProj.p50).toBeLessThanOrEqual(firstProj.p90);
      }
      expect(result.meta.warnings.some((w) => w.includes('Timeline projection ordering violation'))).toBe(true);
    });

    it('should repair p50 > p90 ordering violation', () => {
      const input: EngineCompleteResultV2 = {
        riskScenarioProjections: [
          { date: '2024-01-15', p10: 60, p50: 90, p90: 80, phase: 'Test' },
        ],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      const firstProj = result.timeline.projections[0];
      if (firstProj) {
        expect(firstProj.p10).toBeLessThanOrEqual(firstProj.p50);
        expect(firstProj.p50).toBeLessThanOrEqual(firstProj.p90);
      }
    });

    it('should handle valid timeline ordering without warnings', () => {
      const input: EngineCompleteResultV2 = {
        riskScenarioProjections: [
          { date: '2024-01-15', p10: 60, p50: 70, p90: 80, phase: 'Test' },
        ],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      const firstProj = result.timeline.projections[0];
      if (firstProj) {
        expect(firstProj.p10).toBe(60);
        expect(firstProj.p50).toBe(70);
        expect(firstProj.p90).toBe(80);
      }
      expect(result.meta.warnings.some((w) => w.includes('Timeline projection ordering violation'))).toBe(false);
    });
  });

  // ============================================================
  // TEST F: Invalid dates
  // ============================================================
  describe('F) Invalid dates', () => {
    it('should handle invalid ETD date', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
          etd: 'not-a-date',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.shipment.etd).toBeUndefined();
      expect(result.meta.warnings.some((w) => w.includes('Invalid ETD date'))).toBe(true);
    });

    it('should handle invalid ETA date', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
          eta: 'invalid-date',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.shipment.eta).toBeUndefined();
      expect(result.meta.warnings.some((w) => w.includes('Invalid ETA date'))).toBe(true);
    });

    it('should accept valid ISO dates', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
          etd: '2024-01-15',
          eta: '2024-02-05T10:30:00Z',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.shipment.etd).toBe('2024-01-15');
      expect(result.overview.shipment.eta).toBe('2024-02-05T10:30:00Z');
      expect(result.meta.warnings.some((w) => w.includes('Invalid'))).toBe(false);
    });

    it('should handle null dates', () => {
      const input: EngineCompleteResultV2 = {
        shipment: {
          id: 'SH-TEST',
          etd: null,
          eta: null,
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.shipment.etd).toBeUndefined();
      expect(result.overview.shipment.eta).toBeUndefined();
      // Should not warn for null (expected)
    });

    it('should handle invalid timing optimal window dates', () => {
      const input: EngineCompleteResultV2 = {
        decision_summary: {
          timing: {
            optimal_window: {
              start: 'invalid',
              end: 'invalid',
            },
          },
        },
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.decisions.timing.optimalWindow).toBeNull();
      expect(result.meta.warnings.some((w) => w.includes('Invalid timing optimal window'))).toBe(true);
    });
  });

  // ============================================================
  // ADDITIONAL TESTS
  // ============================================================
  describe('Additional edge cases', () => {
    it('should handle non-object input', () => {
      const result = adaptResultV2(null);

      expect(result.meta.warnings).toContain('Invalid input: expected object');
      expect(result.overview.riskScore.score).toBe(0);
    });

    it('should handle non-object input (string)', () => {
      const result = adaptResultV2('not an object');

      expect(result.meta.warnings).toContain('Invalid input: expected object');
    });

    it('should normalize 0-1 scale to 0-100', () => {
      const input: EngineCompleteResultV2 = {
        profile: {
          factors: {
            delay: 0.7, // 0-1 scale
          },
        },
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.breakdown.factors.delay).toBe(70); // 0.7 -> 70%
    });

    it('should keep 0-100 scale values as-is', () => {
      const input: EngineCompleteResultV2 = {
        profile: {
          factors: {
            delay: 70, // Already 0-100 scale
          },
        },
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.breakdown.factors.delay).toBe(70);
    });

    it('should generate scenario IDs from titles when missing', () => {
      const input: EngineCompleteResultV2 = {
        scenarios: [
          {
            title: 'Add Cargo Insurance',
            category: 'INSURANCE',
            riskReduction: 10,
            costImpact: 500,
          },
        ],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.scenarios[0]?.id).toBe('add-cargo-insurance');
    });

    it('should use fallback scenario ID when title is missing', () => {
      const input: EngineCompleteResultV2 = {
        scenarios: [
          {
            category: 'INSURANCE',
            riskReduction: 10,
            costImpact: 500,
          },
        ],
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.scenarios[0]?.id).toBe('scenario-0');
    });

    it('should clamp negative loss values to 0', () => {
      const input: EngineCompleteResultV2 = {
        loss: {
          p95: -100,
          p99: -200,
          expectedLoss: -50,
          tailContribution: 15,
        },
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.loss?.p95).toBe(0);
      expect(result.loss?.p99).toBe(0);
      expect(result.loss?.expectedLoss).toBe(0);
      expect(result.meta.warnings.some((w) => w.includes('Loss metrics contain negative values'))).toBe(true);
    });

    it('should round risk score to 1 decimal', () => {
      const input: EngineCompleteResultV2 = {
        risk_score: 75.567,
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.score).toBe(75.6);
    });

    it('should round confidence to 0 decimals (percentage)', () => {
      const input: EngineCompleteResultV2 = {
        confidence: 0.856,
        shipment: {
          id: 'SH-TEST',
        },
      };

      const result = adaptResultV2(input);

      expect(result.overview.riskScore.confidence).toBe(86); // 0.856 -> 85.6% -> 86%
    });
  });
});

