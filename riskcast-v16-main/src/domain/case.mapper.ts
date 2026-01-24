/**
 * Case Mapper - Centralized Transformations
 * 
 * Rules:
 * - Input form state → DomainCase (normalize field names, validate, add defaults)
 * - DomainCase → ShipmentData (Summary view model)
 * - DomainCase → ShipmentViewModel (Results view model slice)
 * - All transforms happen here, not in components
 */

import type { DomainCase, Party } from './case.schema';
import type { ShipmentData } from '@/components/summary/types';
import type { ShipmentViewModel } from '@/types/resultsViewModel';
import { getPortInfoWithFallback } from './port-lookup';
import { normalizeTransportMode, normalizePriority } from './case.schema';

/**
 * Map input form data (from HTML form or React state) to DomainCase
 * 
 * Handles field name normalization:
 * - pol_code → pol
 * - cargo_value OR insuranceValue OR shipment_value → cargoValue
 * - transport_mode → transportMode (with enum conversion)
 * - transit_time → transitTimeDays
 * 
 * IMPORTANT: Handles both flat structure (React) and nested structure (input_v20 HTML)
 */
export function mapInputFormToDomainCase(formData: Record<string, unknown>): DomainCase {
  const now = new Date().toISOString();
  const caseId = formData.caseId ? String(formData.caseId) : `CASE-${Date.now()}`;
  
  // CRITICAL: Handle nested structure from Input page (transport.pol, cargo.value, etc.)
  const transport = (formData.transport || {}) as Record<string, unknown>;
  const cargo = (formData.cargo || formData.cargoDetails || {}) as Record<string, unknown>;
  
  // Normalize transport mode (check both flat and nested)
  const transportMode = normalizeTransportMode(
    String(formData.transport_mode || transport.mode || formData.mode || 'AIR')
  );
  
  // Normalize priority
  const priority = normalizePriority(String(formData.priority || transport.priority || 'normal'));
  
  // Handle nested cargo structures from input_v20
  const cargoWeights = (cargo.weights || {}) as Record<string, unknown>;
  const cargoInsurance = (cargo.insurance || {}) as Record<string, unknown>;
  
  // Get cargo value from multiple possible sources (flat and nested)
  // CRITICAL: input_v20 stores value in cargo.insurance.valueUsd internally,
  // but when synced to RISKCAST_STATE it's FLATTENED to cargo.insuranceValue, cargo.value, cargo.cargo_value
  // So we must check BOTH nested and flattened structures
  const cargoValue = Number(formData.cargo_value) ||           // Top-level (from migrateToDomainCase flattening)
                     Number(formData.cargoValue) ||            // Top-level camelCase
                     Number(cargoInsurance.valueUsd) ||        // Nested: cargo.insurance.valueUsd
                     Number(cargo.insuranceValue) ||           // Flattened: cargo.insuranceValue
                     Number(cargo.value) ||                    // Flattened: cargo.value
                     Number(cargo.cargo_value) ||              // Flattened: cargo.cargo_value
                     Number(cargo.cargoValue) ||               // cargo.cargoValue
                     Number(formData.insuranceValue) ||        // Top-level
                     Number(formData.shipment_value) ||        // Legacy
                     Number(formData.value) ||                 // Legacy
                     Number((formData.shipment as Record<string, unknown>)?.valueUSD) ||
                     0;
  
  // Debug log to trace cargo value extraction
  console.log('[mapInputFormToDomainCase] Cargo value extraction:', {
    'formData.cargo_value': formData.cargo_value,
    'formData.cargoValue': formData.cargoValue,
    'cargoInsurance.valueUsd': cargoInsurance.valueUsd,
    'cargo.insuranceValue': cargo.insuranceValue,
    'cargo.value': cargo.value,
    'cargo.cargo_value': cargo.cargo_value,
    'extractedCargoValue': cargoValue,
  });
  
  // Get POL/POD codes (check both flat and nested)
  const pol = String(
    formData.pol_code || 
    transport.pol || 
    formData.pol || 
    formData.origin || 
    'SGN'
  ).toUpperCase();
  const pod = String(
    formData.pod_code || 
    transport.pod || 
    formData.pod || 
    formData.destination || 
    'LAX'
  ).toUpperCase();
  
  // Get ETD/ETA (support both ISO strings and YYYY-MM-DD, check nested structure)
  // CRITICAL: Handle empty strings - if empty string is provided, preserve it as undefined (optional field)
  const etdValue = formData.etd || transport.etd || formData.departureDate || transport.departureDate;
  const etd = etdValue && String(etdValue).trim() !== '' 
    ? String(etdValue) 
    : new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]!;
  
  // Calculate transit time first (needed for ETA calculation if missing)
  // Check multiple field name variations
  const transitTimeValue = formData.transit_time || 
                           formData.transit_time_days || 
                           formData.transitDays ||
                           formData.transitTimeDays ||
                           transport.transitTimeDays || 
                           transport.transit_time_days ||
                           transport.transitTime ||
                           transport.transit_time;
  let transitTimeDays = transitTimeValue != null && transitTimeValue !== '' ? Number(transitTimeValue) : 0;
  
  // Get ETA (check multiple field name variations)
  const etaValue = formData.eta || transport.eta || formData.arrivalDate || transport.arrivalDate;
  let eta: string | undefined = etaValue && String(etaValue).trim() !== '' ? String(etaValue) : undefined;
  
  // If transit time is 0 or missing, try to calculate from ETD/ETA
  if (transitTimeDays === 0 && eta && etd) {
    try {
      const etdDate = new Date(etd);
      const etaDate = new Date(eta);
      if (!isNaN(etdDate.getTime()) && !isNaN(etaDate.getTime())) {
        const days = Math.max(1, Math.ceil((etaDate.getTime() - etdDate.getTime()) / (1000 * 60 * 60 * 24)));
        transitTimeDays = days;
      }
    } catch (e) {
      // Invalid dates, use default based on mode
      transitTimeDays = transportMode === 'AIR' ? 3 : 14;
    }
  }
  
  // If transit time is still 0, set default based on transport mode
  if (transitTimeDays === 0) {
    transitTimeDays = transportMode === 'AIR' ? 3 : 14;
  }
  
  // If ETA is missing but we have ETD and transit time, calculate ETA
  if (!eta && etd && transitTimeDays > 0) {
    try {
      const etdDate = new Date(etd);
      if (!isNaN(etdDate.getTime())) {
        const etaDate = new Date(etdDate.getTime() + transitTimeDays * 24 * 60 * 60 * 1000);
        eta = etaDate.toISOString().split('T')[0];
      }
    } catch (e) {
      // Ignore calculation errors
    }
  }
  
  // Extract seller info (handle both object and flat structure)
  const sellerData = (formData.seller || {}) as Record<string, unknown>;
  const seller_company = formData.seller_company || formData.sellerCompany || formData.seller_company_name;
  const seller_email = formData.seller_email || formData.sellerEmail;
  const seller_phone = formData.seller_phone || formData.sellerPhone;
  const seller_name = formData.seller_name || formData.sellerName || formData.seller_contact_person;
  // Get name: prefer contactPerson (from input_v20) over name
  const sellerContactName = sellerData.contactPerson || sellerData.contact_person || sellerData.name || seller_name;
  const seller: Party = {
    name: sellerContactName ? String(sellerContactName) : undefined,
    company: String(sellerData.company || seller_company || sellerData.companyName || sellerData.company_name || ''),
    email: String(sellerData.email || seller_email || ''),
    phone: String(sellerData.phone || seller_phone || ''),
    country: sellerData.country 
      ? (typeof sellerData.country === 'string' 
          ? sellerData.country 
          : String((sellerData.country as Record<string, unknown>).name || '')) 
      : '',
    city: sellerData.city ? String(sellerData.city) : undefined,
    address: sellerData.address ? String(sellerData.address) : undefined,
    tax_id: sellerData.tax_id || sellerData.taxId ? String(sellerData.tax_id || sellerData.taxId) : undefined,
  };
  
  // Extract buyer info
  const buyerData = (formData.buyer || {}) as Record<string, unknown>;
  const buyer_company = formData.buyer_company || formData.buyerCompany;
  const buyer_email = formData.buyer_email || formData.buyerEmail;
  const buyer_phone = formData.buyer_phone || formData.buyerPhone;
  const buyer_name = formData.buyer_name || formData.buyerName || formData.buyer_contact_person;
  // Get name: prefer contactPerson (from input_v20) over name
  const buyerContactName = buyerData.contactPerson || buyerData.contact_person || buyerData.name || buyer_name;
  const buyer: Party = {
    name: buyerContactName ? String(buyerContactName) : undefined,
    company: String(buyerData.company || buyer_company || buyerData.companyName || buyerData.company_name || ''),
    email: String(buyerData.email || buyer_email || ''),
    phone: String(buyerData.phone || buyer_phone || ''),
    country: buyerData.country 
      ? (typeof buyerData.country === 'string' 
          ? buyerData.country 
          : String((buyerData.country as Record<string, unknown>).name || '')) 
      : '',
    city: buyerData.city ? String(buyerData.city) : undefined,
    address: buyerData.address ? String(buyerData.address) : undefined,
    tax_id: buyerData.tax_id || buyerData.taxId ? String(buyerData.tax_id || buyerData.taxId) : undefined,
  };
  
  // Extract cargo info (already extracted above, but ensure we use it)
  const cargoData = cargo;
  
  // Extract modules (if provided)
  const modulesData = (formData.modules || formData.riskModules || {}) as Record<string, unknown>;
  
  // Build DomainCase
  const domainCase: DomainCase = {
    caseId,
    runId: formData.runId ? String(formData.runId) : undefined,
    version: String(formData.version || '1.0'),
    createdAt: formData.createdAt ? String(formData.createdAt) : now,
    lastModified: now,
    
    pol,
    pod,
    transportMode,
    containerType: String(
      formData.container || 
      transport.container || 
      transport.containerType ||
      formData.container_type || 
      formData.containerType ||
      (transportMode === 'AIR' ? 'Air Cargo Unit' : '40HC')
    ),
    serviceRoute: (formData.service_route || formData.serviceRoute || transport.serviceRoute || transport.service_route) 
      ? String(formData.service_route || formData.serviceRoute || transport.serviceRoute || transport.service_route).trim() || undefined
      : undefined,
    carrier: (formData.carrier || transport.carrier || formData.carrierName || transport.carrierName) 
      ? String(formData.carrier || transport.carrier || formData.carrierName || transport.carrierName).trim() || undefined
      : undefined,
    
    etd,
    eta,
    transitTimeDays,
    
    cargoType: String(
      cargoData.cargo_type || 
      cargoData.cargoType || 
      formData.cargo_type || 
      formData.cargoType ||
      'Electronics'
    ),
    cargoCategory: (cargoData.cargo_category || cargoData.cargoCategory || formData.cargo_category || formData.cargoCategory) 
      ? String(cargoData.cargo_category || cargoData.cargoCategory || formData.cargo_category || formData.cargoCategory) 
      : undefined,
    // CRITICAL: Check flattened fields first (from migrateToDomainCase), then nested structures
    hsCode: (() => {
      const val = formData.hsCode || cargoData.hs_code || cargoData.hsCode || formData.hs_code;
      return val ? String(val).trim() || undefined : undefined;
    })(),
    packaging: (() => {
      const val = formData.packingType || cargoData.packaging || cargoData.packing_type || 
                  cargoData.packingType || formData.packaging || formData.packing_type;
      return val ? String(val).trim() || undefined : undefined;
    })(),
    packages: Number(
      cargoData.packages || 
      cargoData.numberOfPackages || 
      cargoData.packageCount ||
      formData.packages ||
      formData.numberOfPackages ||
      formData.packageCount
    ) || 1,
    // CRITICAL: Check flattened fields first (from migrateToDomainCase), then nested structures
    grossWeightKg: (() => {
      const val = formData.grossWeight || cargoWeights.grossKg || cargoData.gross_weight_kg || 
                  cargoData.grossWeight || cargoData.weight || formData.gross_weight_kg;
      return val != null && val !== '' && val !== 0 ? Number(val) : undefined;
    })(),
    netWeightKg: (() => {
      const val = formData.netWeight || cargoWeights.netKg || cargoData.net_weight_kg || 
                  cargoData.netWeight || formData.net_weight_kg;
      return val != null && val !== '' && val !== 0 ? Number(val) : undefined;
    })(),
    volumeCbm: (() => {
      const val = formData.volumeCbm || cargoData.volumeCbm || cargoData.volume_cbm || 
                  cargoData.volume || cargoData.volumeM3 || formData.volume_cbm || 
                  formData.volume || formData.volumeM3;
      return val != null && val !== '' && val !== 0 ? Number(val) : undefined;
    })(),
    
    cargoValue,
    currency: (formData.currency === 'VND' ? 'VND' : 'USD') as 'USD' | 'VND',
    
    incoterm: formData.incoterm ? String(formData.incoterm) : undefined,
    incotermLocation: formData.incoterm_location || formData.incotermLocation ? String(formData.incoterm_location || formData.incotermLocation) : undefined,
    priority,
    
    seller,
    buyer,
    forwarder: formData.forwarder ? (formData.forwarder as Partial<Party>) : undefined,
    
    modules: {
      // Handle both formats: esg/esgRisk, weather/weatherClimateRisk, etc.
      // If new format exists (esgRisk), use it; otherwise fallback to old format (esg)
      esg: modulesData.esgRisk !== undefined ? Boolean(modulesData.esgRisk) : (modulesData.esg !== false),
      weather: modulesData.weatherClimateRisk !== undefined ? Boolean(modulesData.weatherClimateRisk) : (modulesData.weather !== false),
      portCongestion: modulesData.portCongestionRisk !== undefined 
        ? Boolean(modulesData.portCongestionRisk)
        : (modulesData.portCongestion !== false && modulesData.port !== false),
      carrierPerformance: modulesData.carrierPerformance !== undefined
        ? Boolean(modulesData.carrierPerformance)
        : (modulesData.carrierPerformance !== false && modulesData.carrier !== false),
      marketScanner: modulesData.marketConditionScanner !== undefined
        ? Boolean(modulesData.marketConditionScanner)
        : (modulesData.marketScanner === true || modulesData.market === true),
      insurance: modulesData.insuranceOptimization !== undefined
        ? Boolean(modulesData.insuranceOptimization)
        : (modulesData.insurance !== false),
      // Backwards compatibility: allow top-level 'logistics' flag to map to portCongestion
      logistics: modulesData.logistics !== undefined 
        ? Boolean(modulesData.logistics) 
        : (modulesData.portCongestion !== false && modulesData.port !== false) ||
          (modulesData.portCongestionRisk !== false),
    },
  };
  
  return domainCase;
}

/**
 * Map DomainCase to ShipmentData (for Summary page)
 */
export function mapDomainCaseToShipmentData(domainCase: DomainCase): ShipmentData {
  const polInfo = getPortInfoWithFallback(domainCase.pol);
  const podInfo = getPortInfoWithFallback(domainCase.pod);
  
  // CRITICAL: Preserve 0 values (0 kg, 0 CBM, 0 days are valid)
  // Use ?? only for truly undefined, use || only for empty strings that should be defaults
  return {
    shipmentId: domainCase.caseId,
    trade: {
      pol: domainCase.pol,
      polName: polInfo.name,
      polCity: polInfo.city,
      polCountry: polInfo.country,
      pod: domainCase.pod,
      podName: podInfo.name,
      podCity: podInfo.city,
      podCountry: podInfo.country,
      mode: domainCase.transportMode,
      service_route: domainCase.serviceRoute || `${domainCase.pol}-${domainCase.pod} Direct`,
      carrier: domainCase.carrier || '',
      container_type: domainCase.containerType,
      etd: domainCase.etd,
      // CRITICAL: Empty string '' for optional eta is OK in ShipmentData (vs undefined in DomainCase)
      eta: domainCase.eta || '',
      // CRITICAL: Preserve 0 as valid transit_time_days (0 days is valid, e.g., same-day pickup)
      transit_time_days: domainCase.transitTimeDays ?? 0,
      incoterm: domainCase.incoterm || 'FOB',
      incoterm_location: domainCase.incotermLocation || '',
      priority: domainCase.priority,
    },
    cargo: {
      cargo_type: domainCase.cargoType,
      cargo_category: domainCase.cargoCategory || 'General',
      hs_code: domainCase.hsCode || '',
      hs_chapter: domainCase.hsCode ? domainCase.hsCode.split('.')[0] || '' : '',
      packing_type: domainCase.packaging || '',
      packages: domainCase.packages ?? 1,
      // CRITICAL: Preserve 0 values - 0 kg/0 CBM are valid (empty shipment, documents only, etc.)
      gross_weight_kg: domainCase.grossWeightKg ?? 0,
      net_weight_kg: domainCase.netWeightKg ?? 0,
      volume_cbm: domainCase.volumeCbm ?? 0,
      stackability: false, // Default
      temp_control_required: false, // Default (could be derived from cargoType)
      is_dg: false, // Default (could be derived from hsCode)
    },
    seller: {
      name: domainCase.seller.name || '',
      company: domainCase.seller.company,
      email: domainCase.seller.email,
      phone: domainCase.seller.phone,
      country: domainCase.seller.country,
      city: domainCase.seller.city || '',
      address: domainCase.seller.address || '',
      tax_id: domainCase.seller.tax_id || '',
    },
    buyer: {
      name: domainCase.buyer.name || '',
      company: domainCase.buyer.company,
      email: domainCase.buyer.email,
      phone: domainCase.buyer.phone,
      country: domainCase.buyer.country,
      city: domainCase.buyer.city || '',
      address: domainCase.buyer.address || '',
      tax_id: domainCase.buyer.tax_id || '',
    },
    // CRITICAL: Preserve 0 as valid cargoValue (0 is valid for free samples, documents, etc.)
    value: domainCase.cargoValue ?? 0,
    currency: domainCase.currency,
  };
}

/**
 * Map DomainCase to ShipmentViewModel (for Results page)
 */
export function mapDomainCaseToShipmentViewModel(domainCase: DomainCase): ShipmentViewModel {
  const polInfo = getPortInfoWithFallback(domainCase.pol);
  const podInfo = getPortInfoWithFallback(domainCase.pod);
  
  // Normalize date strings (ensure ISO format or undefined)
  const normalizeDate = (dateStr: string | undefined): string | undefined => {
    if (!dateStr) return undefined;
    // If already ISO format, return as is
    if (dateStr.includes('T')) return dateStr;
    // If YYYY-MM-DD, return unchanged (tests expect YYYY-MM-DD)
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return undefined;
      return date.toISOString();
    } catch {
      return undefined;
    }
  };
  
  return {
    id: domainCase.caseId,
    route: `${domainCase.pol} → ${domainCase.pod}`,
    pol: domainCase.pol,
    pod: domainCase.pod,
    carrier: domainCase.carrier || '',
    etd: normalizeDate(domainCase.etd),
    eta: normalizeDate(domainCase.eta),
    transitTime: domainCase.transitTimeDays,
    container: domainCase.containerType === 'Air Cargo Unit' ? '' : domainCase.containerType || '',
    // If both containerType and cargoType are the library defaults, treat as missing; otherwise preserve values.
    cargo: (domainCase.containerType === 'Air Cargo Unit' && domainCase.cargoType === 'Electronics') ? '' : (domainCase.cargoType || ''),
    cargoType: (domainCase.containerType === 'Air Cargo Unit' && domainCase.cargoType === 'Electronics') ? '' : (domainCase.cargoType || ''),
    containerType: domainCase.containerType === 'Air Cargo Unit' ? '' : domainCase.containerType || '',
    packaging: domainCase.packaging || null,
    incoterm: domainCase.incoterm || '',
    cargoValue: domainCase.cargoValue,
  };
}

/**
 * Map DomainCase to Analyze Request payload expected by backend engine.
 * This function produces a stable, normalized payload (snake_case) so analysis is deterministic.
 */
export function mapDomainCaseToAnalyzeRequest(domainCase: DomainCase): Record<string, unknown> {
  return {
    case_id: domainCase.caseId,
    version: domainCase.version,
    created_at: domainCase.createdAt,
    last_modified: domainCase.lastModified,
    shipment: {
      id: domainCase.caseId,
      pol_code: domainCase.pol,
      pod_code: domainCase.pod,
      origin: domainCase.pol,
      destination: domainCase.pod,
      route: `${domainCase.pol}-${domainCase.pod}`,
      carrier: domainCase.carrier || null,
      etd: domainCase.etd,
      eta: domainCase.eta || null,
      transit_time: domainCase.transitTimeDays,
      container: domainCase.containerType,
      container_type: domainCase.containerType,
      cargo: domainCase.cargoType,
      cargo_type: domainCase.cargoType,
      cargo_value: domainCase.cargoValue,
      value: domainCase.cargoValue,
      currency: domainCase.currency,
      incoterm: domainCase.incoterm || null,
      incoterm_location: domainCase.incotermLocation || null,
      packaging: domainCase.packaging || null,
      packages: domainCase.packages,
      gross_weight_kg: domainCase.grossWeightKg || null,
      net_weight_kg: domainCase.netWeightKg || null,
      volume_cbm: domainCase.volumeCbm || null,
    },
    parties: {
      seller: domainCase.seller || {},
      buyer: domainCase.buyer || {},
      forwarder: domainCase.forwarder || {},
    },
    modules: domainCase.modules || {},
    priority: domainCase.priority,
    transport_mode: domainCase.transportMode,
  };
}
