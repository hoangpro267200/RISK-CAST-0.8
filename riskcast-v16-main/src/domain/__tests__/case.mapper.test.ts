/**
 * Unit Tests: case.mapper.ts
 * 
 * Tests for domain mapper functions:
 * - mapInputFormToDomainCase (normalizes form data)
 * - mapDomainCaseToShipmentData (for Summary page)
 * - mapDomainCaseToShipmentViewModel (for Results page)
 */

import { describe, it, expect } from 'vitest';
import {
  mapInputFormToDomainCase,
  mapDomainCaseToShipmentData,
  mapDomainCaseToShipmentViewModel,
} from '../case.mapper';
import { createDefaultDomainCase, type DomainCase } from '../case.schema';
import type { ShipmentData } from '@/components/summary/types';
import type { ShipmentViewModel } from '@/types/resultsViewModel';

describe('case.mapper', () => {
  // ============================================================
  // TEST A: mapInputFormToDomainCase (normalization)
  // ============================================================
  describe('A) mapInputFormToDomainCase', () => {
    it('should normalize pol_code → pol', () => {
      const formData = { pol_code: 'VNSGN', pod_code: 'CNSHA' };
      const result = mapInputFormToDomainCase(formData);
      expect(result.pol).toBe('VNSGN');
      expect(result.pod).toBe('CNSHA');
    });

    it('should normalize cargo_value → cargoValue', () => {
      const formData = { cargo_value: 50000, currency: 'USD' };
      const result = mapInputFormToDomainCase(formData);
      expect(result.cargoValue).toBe(50000);
      expect(result.currency).toBe('USD');
    });

    it('should handle alternative field names (insuranceValue → cargoValue)', () => {
      const formData = { insuranceValue: 75000, currency: 'VND' };
      const result = mapInputFormToDomainCase(formData);
      expect(result.cargoValue).toBe(75000);
    });

    it('should normalize transport_mode → transportMode enum', () => {
      const formData = { transport_mode: 'sea', mode: 'AIR' };
      const result = mapInputFormToDomainCase(formData);
      expect(['SEA', 'AIR']).toContain(result.transportMode);
    });

    it('should normalize priority → Priority enum', () => {
      const formData = { priority: 'urgent', priority_level: 'normal' };
      const result = mapInputFormToDomainCase(formData);
      expect(['normal', 'express', 'urgent']).toContain(result.priority);
    });

    it('should set default values for missing fields', () => {
      const formData = { pol_code: 'VNSGN' };
      const result = mapInputFormToDomainCase(formData);
      expect(result.version).toBe('1.0');
      expect(result.priority).toBe('normal');
      expect(result.currency).toBe('USD');
    });

    it('should handle dates (etd, eta)', () => {
      const formData = { 
        etd: '2024-01-15', 
        eta: '2024-02-05',
        transit_time_days: 21,
      };
      const result = mapInputFormToDomainCase(formData);
      expect(result.etd).toBe('2024-01-15');
      expect(result.eta).toBe('2024-02-05');
      expect(result.transitTimeDays).toBe(21);
    });

    it('should map party data (seller, buyer, forwarder)', () => {
      const formData = {
        seller_company: 'Seller Co',
        seller_email: 'seller@example.com',
        buyer_company: 'Buyer Co',
        buyer_email: 'buyer@example.com',
      };
      const result = mapInputFormToDomainCase(formData);
      expect(result.seller.company).toBe('Seller Co');
      expect(result.seller.email).toBe('seller@example.com');
      expect(result.buyer.company).toBe('Buyer Co');
      expect(result.buyer.email).toBe('buyer@example.com');
    });

    it('should create caseId if not provided', () => {
      const formData = { pol_code: 'VNSGN' };
      const result = mapInputFormToDomainCase(formData);
      expect(result.caseId).toBeTruthy();
      expect(result.caseId).toMatch(/^CASE-/);
    });

    it('should preserve existing caseId', () => {
      const formData = { caseId: 'CASE-12345', pol_code: 'VNSGN' };
      const result = mapInputFormToDomainCase(formData);
      expect(result.caseId).toBe('CASE-12345');
    });

    it('should set timestamps (createdAt, lastModified)', () => {
      const formData = { pol_code: 'VNSGN' };
      const result = mapInputFormToDomainCase(formData);
      expect(result.createdAt).toBeTruthy();
      expect(result.lastModified).toBeTruthy();
      expect(new Date(result.createdAt).getTime()).toBeLessThanOrEqual(Date.now());
    });

    it('should handle modules state', () => {
      const formData = {
        pol_code: 'VNSGN',
        modules: { insurance: true, logistics: false },
      };
      const result = mapInputFormToDomainCase(formData);
      expect(result.modules.insurance).toBe(true);
      expect(result.modules.logistics).toBe(false);
    });
  });

  // ============================================================
  // TEST B: mapDomainCaseToShipmentData (Summary page)
  // ============================================================
  describe('B) mapDomainCaseToShipmentData', () => {
    it('should map all DomainCase fields to ShipmentData structure', () => {
      const domainCase: DomainCase = {
        ...createDefaultDomainCase(),
        caseId: 'CASE-12345',
        pol: 'VNSGN',
        pod: 'CNSHA',
        transportMode: 'SEA',
        cargoValue: 50000,
        currency: 'USD',
        etd: '2024-01-15',
        transitTimeDays: 21,
        cargoType: 'Electronics',
        packages: 100,
        grossWeightKg: 5000,
      };
      const result = mapDomainCaseToShipmentData(domainCase);
      expect(result.shipmentId).toBe('CASE-12345');
      expect(result.trade.pol).toBe('VNSGN');
      expect(result.trade.pod).toBe('CNSHA');
      expect(result.trade.mode).toBe('SEA');
      expect(result.value).toBe(50000);
      expect(result.currency).toBe('USD');
      expect(result.trade.etd).toBe('2024-01-15');
      expect(result.trade.transit_time_days).toBe(21);
      expect(result.cargo.cargo_type).toBe('Electronics');
      expect(result.cargo.packages).toBe(100);
      expect(result.cargo.gross_weight_kg).toBe(5000);
    });

    it('should preserve nested structures (seller, buyer)', () => {
      const domainCase: DomainCase = {
        ...createDefaultDomainCase(),
        seller: {
          company: 'Seller Co',
          name: 'John Doe',
          email: 'seller@example.com',
          phone: '+1234567890',
          country: 'US',
          city: 'New York',
        },
        buyer: {
          company: 'Buyer Co',
          name: 'Jane Smith',
          email: 'buyer@example.com',
          phone: '+9876543210',
          country: 'VN',
          city: 'Ho Chi Minh',
        },
      };
      const result = mapDomainCaseToShipmentData(domainCase);
      expect(result.seller.company).toBe('Seller Co');
      expect(result.seller.name).toBe('John Doe');
      expect(result.seller.email).toBe('seller@example.com');
      expect(result.buyer.company).toBe('Buyer Co');
      expect(result.buyer.email).toBe('buyer@example.com');
    });

    it('should map container and cargo types correctly', () => {
      const domainCase: DomainCase = {
        ...createDefaultDomainCase(),
        containerType: '40HC',
        cargoType: 'Electronics',
        cargoCategory: 'General',
      };
      const result = mapDomainCaseToShipmentData(domainCase);
      expect(result.trade.container_type).toBe('40HC');
      expect(result.cargo.cargo_type).toBe('Electronics');
    });
  });

  // ============================================================
  // TEST C: mapDomainCaseToShipmentViewModel (Results page)
  // ============================================================
  describe('C) mapDomainCaseToShipmentViewModel', () => {
    it('should map DomainCase to ShipmentViewModel structure', () => {
      const domainCase: DomainCase = {
        ...createDefaultDomainCase(),
        caseId: 'CASE-12345',
        pol: 'VNSGN',
        pod: 'CNSHA',
        transportMode: 'SEA',
        cargoValue: 50000,
        etd: '2024-01-15',
        eta: '2024-02-05',
        transitTimeDays: 21,
        containerType: '40HC',
        cargoType: 'Electronics',
      };
      const result = mapDomainCaseToShipmentViewModel(domainCase);
      expect(result.id).toContain('CASE-12345');
      expect(result.pol).toBe('VNSGN');
      expect(result.pod).toBe('CNSHA');
      expect(result.etd).toBe('2024-01-15');
      expect(result.eta).toBe('2024-02-05');
      expect(result.transitTime).toBe(21);
      expect(result.containerType).toBe('40HC');
      expect(result.cargoType).toBe('Electronics');
      expect(result.cargoValue).toBe(50000);
    });

    it('should build route string from pol and pod', () => {
      const domainCase: DomainCase = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
      };
      const result = mapDomainCaseToShipmentViewModel(domainCase);
      expect(result.route).toContain('VNSGN');
      expect(result.route).toContain('CNSHA');
    });

    it('should handle missing optional fields gracefully', () => {
      const domainCase: DomainCase = {
        ...createDefaultDomainCase(),
        pol: 'VNSGN',
        pod: 'CNSHA',
        // eta, containerType, cargoType not provided
      };
      const result = mapDomainCaseToShipmentViewModel(domainCase);
      expect(result.pol).toBe('VNSGN');
      expect(result.pod).toBe('CNSHA');
      expect(result.eta).toBeUndefined();
      expect(result.containerType).toBe('');
      expect(result.cargoType).toBe('');
    });
  });

  // ============================================================
  // TEST D: Round-trip consistency
  // ============================================================
  describe('D) Round-trip consistency', () => {
    it('should preserve data through DomainCase → ShipmentData → (reverse)', () => {
      const domainCase: DomainCase = {
        ...createDefaultDomainCase(),
        caseId: 'CASE-TEST',
        pol: 'VNSGN',
        pod: 'CNSHA',
        cargoValue: 50000,
      };
      const shipmentData = mapDomainCaseToShipmentData(domainCase);
      // Reverse mapping: ShipmentData → DomainCase
      const formData = {
        caseId: shipmentData.shipmentId,
        pol_code: shipmentData.trade.pol,
        pod_code: shipmentData.trade.pod,
        cargo_value: shipmentData.value,
      };
      const roundTripDomainCase = mapInputFormToDomainCase(formData);
      expect(roundTripDomainCase.pol).toBe(domainCase.pol);
      expect(roundTripDomainCase.pod).toBe(domainCase.pod);
      expect(roundTripDomainCase.cargoValue).toBe(domainCase.cargoValue);
    });
  });
});
