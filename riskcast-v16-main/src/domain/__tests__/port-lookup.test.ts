/**
 * Unit Tests: port-lookup.ts
 * 
 * Tests for port lookup utilities:
 * - getPortInfo (port code → PortInfo)
 * - getPortInfoWithFallback (always returns PortInfo)
 * - searchPorts (query → PortInfo[])
 */

import { describe, it, expect } from 'vitest';
import {
  getPortInfo,
  getPortInfoWithFallback,
  searchPorts,
  type PortInfo,
} from '../port-lookup';

describe('port-lookup', () => {
  // ============================================================
  // TEST A: getPortInfo
  // ============================================================
  describe('A) getPortInfo', () => {
    it('should return PortInfo for valid airport code', () => {
      const result = getPortInfo('SGN');
      expect(result).toBeTruthy();
      expect(result?.code).toBe('SGN');
      expect(result?.type).toBe('airport');
    });

    it('should return PortInfo for valid seaport code', () => {
      const result = getPortInfo('CNSHA');
      expect(result).toBeTruthy();
      expect(result?.code).toBe('CNSHA');
      expect(result?.type).toBe('seaport');
    });

    it('should return null for unknown port code', () => {
      const result = getPortInfo('UNKNOWN');
      expect(result).toBeNull();
    });

    it('should handle null/undefined input', () => {
      expect(getPortInfo(null)).toBeNull();
      expect(getPortInfo(undefined)).toBeNull();
      expect(getPortInfo('')).toBeNull();
    });

    it('should be case-insensitive', () => {
      const upper = getPortInfo('SGN');
      const lower = getPortInfo('sgn');
      const mixed = getPortInfo('Sgn');
      expect(upper?.code).toBe('SGN');
      expect(lower?.code).toBe('SGN');
      expect(mixed?.code).toBe('SGN');
    });
  });

  // ============================================================
  // TEST B: getPortInfoWithFallback
  // ============================================================
  describe('B) getPortInfoWithFallback', () => {
    it('should return PortInfo for valid code', () => {
      const result = getPortInfoWithFallback('SGN');
      expect(result.code).toBe('SGN');
      expect(result.type).toBe('airport');
    });

    it('should return fallback PortInfo for unknown code', () => {
      const result = getPortInfoWithFallback('UNKNOWN');
      expect(result.code).toBe('UNKNOWN');
      expect(result.name).toBe('Unknown Port');
      expect(result.city).toBe('Unknown');
      expect(result.country).toBe('Unknown');
    });

    it('should never return null (always returns PortInfo)', () => {
      expect(getPortInfoWithFallback(null)).toBeTruthy();
      expect(getPortInfoWithFallback(undefined)).toBeTruthy();
      expect(getPortInfoWithFallback('')).toBeTruthy();
    });
  });

  // ============================================================
  // TEST C: searchPorts
  // ============================================================
  describe('C) searchPorts', () => {
    it('should search by port code', () => {
      const results = searchPorts('SGN');
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].code).toContain('SGN');
    });

    it('should search by city name', () => {
      const results = searchPorts('Ho Chi Minh');
      expect(results.length).toBeGreaterThan(0);
      expect(results.some(p => p.city.toLowerCase().includes('ho chi minh'))).toBe(true);
    });

    it('should search by country name', () => {
      const results = searchPorts('Vietnam');
      expect(results.length).toBeGreaterThan(0);
      expect(results.some(p => p.country.toLowerCase().includes('vietnam'))).toBe(true);
    });

    it('should limit results by limit parameter', () => {
      const results = searchPorts('', 5);
      expect(results.length).toBeLessThanOrEqual(5);
    });

    it('should return empty array for no matches', () => {
      const results = searchPorts('XYZABC123');
      expect(results.length).toBe(0);
    });

    it('should be case-insensitive', () => {
      const upper = searchPorts('SGN');
      const lower = searchPorts('sgn');
      expect(upper.length).toBe(lower.length);
    });
  });

  // ============================================================
  // TEST D: PortInfo structure
  // ============================================================
  describe('D) PortInfo structure', () => {
    it('should have all required fields', () => {
      const port = getPortInfo('SGN');
      expect(port).toBeTruthy();
      if (port) {
        expect(port.code).toBeTruthy();
        expect(port.name).toBeTruthy();
        expect(port.city).toBeTruthy();
        expect(port.country).toBeTruthy();
        expect(port.countryCode).toBeTruthy();
        expect(['airport', 'seaport']).toContain(port.type);
      }
    });

    it('should have consistent country/countryCode', () => {
      const port = getPortInfo('CNSHA');
      expect(port).toBeTruthy();
      if (port) {
        // If country is "China", countryCode should be "CN"
        if (port.country.toLowerCase().includes('china')) {
          expect(port.countryCode).toBe('CN');
        }
      }
    });
  });
});
