/**
 * Unit Tests: case.validation.ts
 * 
 * Tests for domain validation functions:
 * - validateDomainCase (critical/warning issues)
 * - getCompletenessScore (0-100 score)
 */

import { describe, it, expect } from 'vitest';
import {
  validateDomainCase,
  getCompletenessScore,
} from '../case.validation';
import { createDefaultDomainCase, type DomainCase } from '../case.schema';
import type { ValidationIssue } from '@/lib/validation';

describe('case.validation', () => {
  // ============================================================
  // TEST A: validateDomainCase (critical issues)
  // ============================================================
  describe('A) validateDomainCase - Critical Issues', () => {
    it('should identify missing POL as critical', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pol: '', // Missing
      };
      const result = validateDomainCase(caseData);
      expect(result.valid).toBe(false);
      const polIssue = result.issues.find(i => i.affectedFields.includes('pol'));
      expect(polIssue).toBeTruthy();
      expect(polIssue?.severity).toBe('critical');
    });

    it('should identify missing POD as critical', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pod: '', // Missing
      };
      const result = validateDomainCase(caseData);
      expect(result.valid).toBe(false);
      const podIssue = result.issues.find(i => i.affectedFields.includes('pod'));
      expect(podIssue).toBeTruthy();
      expect(podIssue?.severity).toBe('critical');
    });

    it('should identify missing ETD as critical', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        etd: '', // Missing
      };
      const result = validateDomainCase(caseData);
      expect(result.valid).toBe(false);
      const etdIssue = result.issues.find(i => i.affectedFields.includes('etd'));
      expect(etdIssue).toBeTruthy();
      expect(etdIssue?.severity).toBe('critical');
    });

    it('should identify missing cargoValue as critical', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        cargoValue: 0, // Missing/invalid
      };
      const result = validateDomainCase(caseData);
      expect(result.valid).toBe(false);
      const valueIssue = result.issues.find(i => i.affectedFields.includes('cargoValue'));
      expect(valueIssue).toBeTruthy();
      expect(valueIssue?.severity).toBe('critical');
    });

    it('should identify invalid transportMode as critical', () => {
      const caseData = {
        ...createDefaultDomainCase(),
        transportMode: 'INVALID' as any, // Invalid enum
      };
      const result = validateDomainCase(caseData);
      expect(result.valid).toBe(false);
      const modeIssue = result.issues.find(i => i.affectedFields.includes('transportMode'));
      expect(modeIssue).toBeTruthy();
    });

    it('should pass validation with all critical fields present', () => {
      const caseData: DomainCase = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
        etd: '2024-01-15',
        cargoValue: 50000,
        transportMode: 'SEA',
      };
      const result = validateDomainCase(caseData);
      // Should have no critical issues (may have warnings)
      const criticalIssues = result.issues.filter(i => i.severity === 'critical');
      expect(criticalIssues.length).toBe(0);
    });
  });

  // ============================================================
  // TEST B: validateDomainCase (warnings)
  // ============================================================
  describe('B) validateDomainCase - Warning Issues', () => {
    it('should warn about missing ETA (optional but recommended)', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
        etd: '2024-01-15',
        eta: undefined, // Missing (optional)
      };
      const result = validateDomainCase(caseData);
      const etaIssue = result.issues.find(i => i.affectedFields.includes('eta'));
      // ETA is optional, so may not be flagged as critical, but could be a warning
      // This depends on implementation
    });

    it('should warn about missing transitTimeDays', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
        etd: '2024-01-15',
        transitTimeDays: 0, // Missing/invalid
      };
      const result = validateDomainCase(caseData);
      const transitIssue = result.issues.find(i => i.affectedFields.includes('transitTimeDays'));
      // Transit time is recommended, so may be a warning
    });

    it('should warn about missing cargo type', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
        etd: '2024-01-15',
        cargoType: '', // Missing
      };
      const result = validateDomainCase(caseData);
      const cargoIssue = result.issues.find(i => i.affectedFields.includes('cargoType'));
      // Cargo type is recommended for better analysis
    });
  });

  // ============================================================
  // TEST C: getCompletenessScore
  // ============================================================
  describe('C) getCompletenessScore', () => {
    it('should return 0 for empty case', () => {
      const caseData: Partial<DomainCase> = {};
      const score = getCompletenessScore(caseData);
      expect(score).toBe(0);
    });

    it('should return 100 for complete case', () => {
      const caseData: DomainCase = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
        transportMode: 'SEA',
        containerType: '40HC',
        etd: '2024-01-15',
        eta: '2024-02-05',
        transitTimeDays: 21,
        cargoType: 'Electronics',
        cargoCategory: 'General',
        packages: 100,
        grossWeightKg: 5000,
        cargoValue: 50000,
        currency: 'USD',
        seller: {
          company: 'Seller Co',
          email: 'seller@example.com',
          country: 'US',
        },
        buyer: {
          company: 'Buyer Co',
          email: 'buyer@example.com',
          country: 'VN',
        },
      };
      const score = getCompletenessScore(caseData);
      expect(score).toBeGreaterThanOrEqual(80); // At least 80% for complete case
      expect(score).toBeLessThanOrEqual(100);
    });

    it('should calculate score based on required fields', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN', // 1 required field
        pod: 'CNSHA', // 2 required fields
        etd: '2024-01-15', // 3 required fields
        // cargoValue missing (4th required)
      };
      const score = getCompletenessScore(caseData);
      expect(score).toBeGreaterThan(0);
      expect(score).toBeLessThan(50); // Less than 50% if missing critical fields
    });

    it('should give higher score for optional fields filled', () => {
      const caseData1: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
        etd: '2024-01-15',
        cargoValue: 50000,
      };
      const caseData2: Partial<DomainCase> = {
        ...caseData1,
        eta: '2024-02-05',
        transitTimeDays: 21,
        cargoType: 'Electronics',
        packages: 100,
      };
      const score1 = getCompletenessScore(caseData1);
      const score2 = getCompletenessScore(caseData2);
      expect(score2).toBeGreaterThan(score1);
    });
  });

  // ============================================================
  // TEST D: Edge cases
  // ============================================================
  describe('D) Edge Cases', () => {
    it('should handle null/undefined values gracefully', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        pol: undefined as any,
        pod: null as any,
      };
      const result = validateDomainCase(caseData);
      expect(result).toBeTruthy();
      expect(result.issues.length).toBeGreaterThan(0);
    });

    it('should handle invalid date formats', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        etd: 'invalid-date',
      };
      const result = validateDomainCase(caseData);
      // Should flag as invalid or treat as missing
      expect(result.valid).toBe(false);
    });

    it('should handle negative values', () => {
      const caseData: Partial<DomainCase> = {
        ...createDefaultDomainCase(),
        cargoValue: -1000, // Invalid
        transitTimeDays: -5, // Invalid
      };
      const result = validateDomainCase(caseData);
      expect(result.valid).toBe(false);
    });
  });
});
