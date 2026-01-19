import type { DomainCase } from './case.schema';
import { createDefaultDomainCase } from './case.schema';
import { mapInputFormToDomainCase } from './case.mapper';

export const STORAGE_KEY = 'RISKCAST_CASE_V1';
export const LEGACY_KEY = 'RISKCAST_STATE';

/**
 * Migrate legacy raw state (Input/Summary/legacy DomainCase) to canonical DomainCase.
 * Uses existing mapper to avoid duplicating normalization logic.
 */
export function migrateToDomainCase(raw: unknown): DomainCase {
  try {
    if (!raw || typeof raw !== 'object') {
      console.log('[migrateToDomainCase] Raw data is not an object, using defaults');
      return createDefaultDomainCase();
    }

    const obj = raw as Record<string, unknown>;
    console.log('[migrateToDomainCase] Input data structure:', {
      hasCaseId: !!obj.caseId,
      hasTransportMode: !!obj.transportMode,
      hasPol: !!obj.pol,
      hasTransport: !!obj.transport,
      hasCargo: !!obj.cargo,
      transportKeys: obj.transport ? Object.keys(obj.transport as Record<string, unknown>) : [],
      cargoKeys: obj.cargo ? Object.keys(obj.cargo as Record<string, unknown>) : [],
    });

    // If it already looks like a DomainCase (has caseId or transportMode), try to coerce minimal fields
    if (obj.caseId || obj.transportMode || obj.pol) {
      console.log('[migrateToDomainCase] Detected DomainCase-like structure, coercing...');
      // Ensure required defaults exist
      const base = (obj as unknown) as DomainCase;
      const now = new Date().toISOString();
      const result = {
        ...createDefaultDomainCase(),
        ...base,
        caseId: base.caseId || `CASE-${Date.now()}`,
        version: base.version || '1.0',
        createdAt: base.createdAt || now,
        lastModified: now,
      };
      console.log('[migrateToDomainCase] Coerced DomainCase:', result);
      return result;
    }

    // Otherwise treat as input form state and map via mapper
    console.log('[migrateToDomainCase] Treating as input form state, mapping via mapper...');
    const result = mapInputFormToDomainCase(obj);
    console.log('[migrateToDomainCase] Mapped DomainCase:', result);
    return result;
  } catch (e) {
    console.error('[migrateToDomainCase] Error during migration:', e);
    // Fallback
    return createDefaultDomainCase();
  }
}

/**
 * Load DomainCase from localStorage with backward-compatible migration:
 * 1) Try STORAGE_KEY (canonical)
 * 2) Else try LEGACY_KEY and migrate
 * 3) Else return null
 *
 * If migration from legacy succeeds, save canonical copy to STORAGE_KEY.
 */
export function loadDomainCaseFromStorage(): DomainCase | null {
  if (typeof window === 'undefined') return null;

  try {
    const canonical = localStorage.getItem(STORAGE_KEY);
    if (canonical) {
      console.log('[loadDomainCaseFromStorage] Found canonical case in', STORAGE_KEY);
      const parsed = JSON.parse(canonical);
      return migrateToDomainCase(parsed);
    }

    const legacy = localStorage.getItem(LEGACY_KEY);
    if (legacy) {
      console.log('[loadDomainCaseFromStorage] Found legacy case in', LEGACY_KEY, 'migrating...');
      try {
        const parsed = JSON.parse(legacy);
        console.log('[loadDomainCaseFromStorage] Legacy data sample:', {
          hasTransport: !!parsed.transport,
          hasCargo: !!parsed.cargo,
          transportEta: parsed.transport?.eta,
          transportTransitTimeDays: parsed.transport?.transitTimeDays,
          transportCarrier: parsed.transport?.carrier,
          cargoHsCode: parsed.cargo?.hsCode,
          cargoPackingType: parsed.cargo?.packingType,
        });
        const migrated = migrateToDomainCase(parsed);
        console.log('[loadDomainCaseFromStorage] Migrated DomainCase:', {
          eta: migrated.eta,
          transitTimeDays: migrated.transitTimeDays,
          carrier: migrated.carrier,
          hsCode: migrated.hsCode,
          packaging: migrated.packaging,
        });
        // Save canonical copy for future loads
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated));
          console.log('[loadDomainCaseFromStorage] Saved canonical copy to', STORAGE_KEY);
        } catch (e) {
          console.warn('[loadDomainCaseFromStorage] Failed to save canonical copy:', e);
        }
        return migrated;
      } catch (e) {
        console.error('[loadDomainCaseFromStorage] Failed to parse/migrate legacy data:', e);
        // ignore parse error and fallback
      }
    } else {
      console.log('[loadDomainCaseFromStorage] No data found in', LEGACY_KEY, 'or', STORAGE_KEY);
    }
  } catch (e) {
    console.error('[loadDomainCaseFromStorage] localStorage access error:', e);
    // ignore localStorage access errors
  }

  return null;
}

export function saveDomainCaseToStorage(domainCase: DomainCase): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(domainCase));
  } catch (e) {
    // ignore storage failures
  }
}



