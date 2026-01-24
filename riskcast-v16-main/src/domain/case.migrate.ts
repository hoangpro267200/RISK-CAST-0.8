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
    
    // Flatten nested structure from input_v20 (transport.*, cargo.*)
    const transport = (obj.transport || {}) as Record<string, unknown>;
    const cargo = (obj.cargo || {}) as Record<string, unknown>;
    const cargoWeights = (cargo.weights || {}) as Record<string, unknown>;
    // CRITICAL: cargo.insurance may be nested OR flattened to cargo level
    const cargoInsurance = (cargo.insurance || {}) as Record<string, unknown>;
    
    // CRITICAL FIX: Get cargoValue from BOTH nested (cargo.insurance.valueUsd) 
    // AND flattened (cargo.insuranceValue, cargo.value, cargo.cargo_value) structures
    // input_v20's StateManager flattens cargo.insurance.valueUsd to cargo.insuranceValue when syncing to RISKCAST_STATE
    const extractedCargoValue = 
      Number(cargoInsurance.valueUsd) ||  // Nested: cargo.insurance.valueUsd
      Number(cargo.insuranceValue) ||     // Flattened: cargo.insuranceValue
      Number(cargo.value) ||              // Flattened: cargo.value
      Number(cargo.cargo_value) ||        // Flattened: cargo.cargo_value
      Number(obj.cargoValue) ||           // Top-level from DomainCase
      Number(obj.cargo_value) ||          // Top-level from DomainCase (snake_case)
      0;
    
    console.log('[migrateToDomainCase] Input data structure:', {
      hasCaseId: !!obj.caseId,
      hasTransportMode: !!obj.transportMode,
      hasPol: !!obj.pol,
      hasTransport: !!obj.transport,
      hasCargo: !!obj.cargo,
      transportKeys: transport ? Object.keys(transport) : [],
      cargoKeys: cargo ? Object.keys(cargo) : [],
      transitTimeDays: transport.transitTimeDays || transport.transitTime || obj.transitDays,
      eta: transport.eta || obj.eta,
      carrier: transport.carrier || obj.carrier,
      hsCode: cargo.hsCode || obj.hsCode,
      packingType: cargo.packingType || cargo.packaging || obj.packaging,
      // DEBUG: Show all possible cargo value sources
      cargoValueSources: {
        'cargoInsurance.valueUsd': cargoInsurance.valueUsd,
        'cargo.insuranceValue': cargo.insuranceValue,
        'cargo.value': cargo.value,
        'cargo.cargo_value': cargo.cargo_value,
        'obj.cargoValue': obj.cargoValue,
      },
      extractedCargoValue,
      grossWeight: cargoWeights.grossKg || cargo.grossWeight || cargo.weight,
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

    // Extract seller/buyer data for flattening
    const seller = (obj.seller || {}) as Record<string, unknown>;
    const buyer = (obj.buyer || {}) as Record<string, unknown>;
    
    // Flatten nested structures into top-level for mapInputFormToDomainCase
    // CRITICAL: The mapper expects certain field names at various levels
    const flattenedObj = {
      ...obj,
      // Flatten transport fields to top level
      transitDays: transport.transitTimeDays || transport.transitTime || obj.transitDays,
      eta: transport.eta || obj.eta,
      carrier: transport.carrier || obj.carrier,
      mode: transport.mode || transport.modeOfTransport || obj.mode,
      containerType: transport.containerType || obj.containerType,
      incoterm: transport.incoterm || obj.incoterm,
      incotermLocation: transport.incotermLocation || obj.incotermLocation,
      
      // Flatten cargo fields to top level
      hsCode: cargo.hsCode || obj.hsCode,
      packingType: cargo.packingType || cargo.packaging || obj.packaging,
      cargoType: cargo.cargoType || obj.cargoType,
      packages: cargo.numberOfPackages || cargo.packageCount || obj.packages,
      volumeCbm: cargo.volumeCbm || cargo.volumeM3 || cargo.volume || obj.volumeCbm,
      
      // Flatten cargo.weights to top level
      grossWeight: cargoWeights.grossKg || cargo.grossWeight || cargo.weight || obj.grossWeight,
      netWeight: cargoWeights.netKg || cargo.netWeight || obj.netWeight,
      
      // CRITICAL: Use pre-extracted cargoValue that checks BOTH nested and flattened structures
      cargoValue: extractedCargoValue,
      insuranceValue: extractedCargoValue,
      cargo_value: extractedCargoValue,
      
      // Ensure seller data is properly structured with name from contactPerson
      seller: {
        ...seller,
        name: seller.contactPerson || seller.name || seller.contact_person,
        company: seller.companyName || seller.company || seller.company_name,
        country: typeof seller.country === 'object' 
          ? (seller.country as Record<string, unknown>).name || '' 
          : seller.country || '',
      },
      
      // Ensure buyer data is properly structured with name from contactPerson
      buyer: {
        ...buyer,
        name: buyer.contactPerson || buyer.name || buyer.contact_person,
        company: buyer.companyName || buyer.company || buyer.company_name,
        country: typeof buyer.country === 'object' 
          ? (buyer.country as Record<string, unknown>).name || '' 
          : buyer.country || '',
      },
    };

    // Treat as input form state and map via mapper
    console.log('[migrateToDomainCase] Treating as input form state, mapping via mapper...');
    console.log('[migrateToDomainCase] Flattened fields:', {
      transitDays: flattenedObj.transitDays,
      eta: flattenedObj.eta,
      carrier: flattenedObj.carrier,
      hsCode: flattenedObj.hsCode,
      packingType: flattenedObj.packingType,
      cargoValue: flattenedObj.cargoValue,
      grossWeight: flattenedObj.grossWeight,
      volumeCbm: flattenedObj.volumeCbm,
      sellerName: flattenedObj.seller?.name,
      buyerName: flattenedObj.buyer?.name,
    });
    
    const result = mapInputFormToDomainCase(flattenedObj);
    console.log('[migrateToDomainCase] Mapped DomainCase:', {
      eta: result.eta,
      transitTimeDays: result.transitTimeDays,
      carrier: result.carrier,
      hsCode: result.hsCode,
      packaging: result.packaging,
      cargoValue: result.cargoValue,
      grossWeightKg: result.grossWeightKg,
      volumeCbm: result.volumeCbm,
      sellerName: result.seller?.name,
      buyerName: result.buyer?.name,
    });
    return result;
  } catch (e) {
    console.error('[migrateToDomainCase] Error during migration:', e);
    // Fallback
    return createDefaultDomainCase();
  }
}

/**
 * Load DomainCase from localStorage with backward-compatible migration:
 * 
 * PRIORITY ORDER (CRITICAL FIX):
 * 1) ALWAYS try LEGACY_KEY (RISKCAST_STATE) first - this is the LIVE INPUT DATA
 * 2) Only if no RISKCAST_STATE, fall back to STORAGE_KEY (RISKCAST_CASE_V1)
 * 
 * This ensures fresh data from input form always takes precedence over cached data.
 */
export function loadDomainCaseFromStorage(): DomainCase | null {
  if (typeof window === 'undefined') return null;

  try {
    // CRITICAL: Always check RISKCAST_STATE first (live input form data)
    const legacy = localStorage.getItem(LEGACY_KEY);
    if (legacy) {
      console.log('[loadDomainCaseFromStorage] Found RISKCAST_STATE (input form data), migrating...');
      try {
        const parsed = JSON.parse(legacy);
        console.log('[loadDomainCaseFromStorage] RISKCAST_STATE data sample:', {
          hasTransport: !!parsed.transport,
          hasCargo: !!parsed.cargo,
          transportEta: parsed.transport?.eta,
          transportTransitTimeDays: parsed.transport?.transitTimeDays || parsed.transport?.transitTime,
          transportCarrier: parsed.transport?.carrier,
          cargoHsCode: parsed.cargo?.hsCode,
          cargoPackingType: parsed.cargo?.packingType || parsed.cargo?.packaging,
          cargoWeights: parsed.cargo?.weights,
          cargoVolume: parsed.cargo?.volumeCbm || parsed.cargo?.volume || parsed.cargo?.volumeM3,
          cargoInsurance: parsed.cargo?.insurance,
          cargoValue: parsed.cargo?.insurance?.valueUsd || parsed.cargo?.value || parsed.cargo?.cargo_value,
          sellerContactPerson: parsed.seller?.contactPerson,
          buyerContactPerson: parsed.buyer?.contactPerson,
        });
        const migrated = migrateToDomainCase(parsed);
        console.log('[loadDomainCaseFromStorage] Migrated DomainCase:', {
          eta: migrated.eta,
          transitTimeDays: migrated.transitTimeDays,
          carrier: migrated.carrier,
          hsCode: migrated.hsCode,
          packaging: migrated.packaging,
          cargoValue: migrated.cargoValue,
          grossWeightKg: migrated.grossWeightKg,
          volumeCbm: migrated.volumeCbm,
          sellerName: migrated.seller?.name,
          buyerName: migrated.buyer?.name,
        });
        // Save canonical copy
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated));
          console.log('[loadDomainCaseFromStorage] Saved canonical copy to', STORAGE_KEY);
        } catch (e) {
          console.warn('[loadDomainCaseFromStorage] Failed to save canonical copy:', e);
        }
        return migrated;
      } catch (e) {
        console.error('[loadDomainCaseFromStorage] Failed to parse/migrate RISKCAST_STATE:', e);
        // Fall through to try RISKCAST_CASE_V1
      }
    }

    // Fallback: Try RISKCAST_CASE_V1 (previously migrated canonical data)
    const canonical = localStorage.getItem(STORAGE_KEY);
    if (canonical) {
      console.log('[loadDomainCaseFromStorage] No RISKCAST_STATE, using cached', STORAGE_KEY);
      const parsed = JSON.parse(canonical);
      // If it's already a DomainCase, just return it with minimal coercion
      if (parsed.caseId && parsed.transportMode) {
        return { ...createDefaultDomainCase(), ...parsed };
      }
      return migrateToDomainCase(parsed);
    }

    console.log('[loadDomainCaseFromStorage] No data found in', LEGACY_KEY, 'or', STORAGE_KEY);
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



