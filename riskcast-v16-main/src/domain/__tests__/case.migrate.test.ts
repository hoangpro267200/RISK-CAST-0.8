import { describe, it, expect, beforeEach } from 'vitest';
import { migrateToDomainCase, loadDomainCaseFromStorage, saveDomainCaseToStorage, STORAGE_KEY, LEGACY_KEY } from '../case.migrate';
import { mapInputFormToDomainCase } from '../case.mapper';

describe('case.migrate', () => {
  beforeEach(() => {
    // Clear storage between tests (vitest uses jsdom)
    try {
      localStorage.clear();
    } catch {}
  });

  it('migrates input form shape to DomainCase and normalizes fields', () => {
    const raw = {
      pol_code: 'sgn',
      pod_code: 'lax',
      transport_mode: 'air',
      cargo_value: '125000',
      container: 'Air Cargo Unit',
      etd: '2026-02-01',
      packages: 10,
      seller: { company: 'S Co' },
      buyer: { company: 'B Co' },
    };

    const domain = migrateToDomainCase(raw);
    expect(domain.pol).toBe('SGN');
    expect(domain.pod).toBe('LAX');
    expect(domain.transportMode).toBe('AIR');
    expect(domain.cargoValue).toBe(125000);
    expect(domain.containerType).toBe('Air Cargo Unit');
    expect(domain.packages).toBe(10);
  });

  it('preserves DomainCase-like object and fills defaults', () => {
    const nowId = `CASE-TEST-${Date.now()}`;
    const rawDomain = {
      caseId: nowId,
      pol: 'SGN',
      pod: 'LAX',
      transportMode: 'AIR',
      containerType: '40HC',
      etd: '2026-02-02',
      packages: 2,
      cargoValue: 5000,
      seller: { company: 'S' },
      buyer: { company: 'B' },
    };

    const migrated = migrateToDomainCase(rawDomain);
    expect(migrated.caseId).toBe(nowId);
    expect(migrated.containerType).toBe('40HC');
    expect(migrated.cargoValue).toBe(5000);
  });

  it('saves and loads canonical DomainCase to storage (backward-compatible)', () => {
    const form = {
      pol_code: 'SGN',
      pod_code: 'LAX',
      transport_mode: 'sea',
      cargo_value: 2000,
      container: '40HC',
      seller: { company: 'Seller' },
      buyer: { company: 'Buyer' },
    };
    const domain = mapInputFormToDomainCase(form);

    saveDomainCaseToStorage(domain);
    const loaded = loadDomainCaseFromStorage();
    expect(loaded).not.toBeNull();
    expect(loaded?.pol).toBe(domain.pol);
    expect(loaded?.pod).toBe(domain.pod);
    expect(loaded?.cargoValue).toBe(domain.cargoValue);
  });
});


