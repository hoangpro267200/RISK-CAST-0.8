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
 */
export function mapInputFormToDomainCase(formData: Record<string, unknown>): DomainCase {
  const now = new Date().toISOString();
  const caseId = `CASE-${Date.now()}`;
  
  // Normalize transport mode
  const transportMode = normalizeTransportMode(
    String(formData.transport_mode || formData.mode || 'AIR')
  );
  
  // Normalize priority
  const priority = normalizePriority(String(formData.priority || 'normal'));
  
  // Get cargo value from multiple possible sources
  const cargoValue = Number(formData.cargo_value) ||
                     Number(formData.insuranceValue) ||
                     Number(formData.shipment_value) ||
                     Number(formData.value) ||
                     0;
  
  // Get POL/POD codes
  const pol = String(formData.pol_code || formData.pol || formData.origin || 'SGN').toUpperCase();
  const pod = String(formData.pod_code || formData.pod || formData.destination || 'LAX').toUpperCase();
  
  // Get ETD/ETA (support both ISO strings and YYYY-MM-DD)
  const etd = formData.etd ? String(formData.etd) : new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]!;
  const eta = formData.eta ? String(formData.eta) : undefined;
  
  // Calculate transit time if not provided
  let transitTimeDays = Number(formData.transit_time) || Number(formData.transit_time_days) || 0;
  if (transitTimeDays === 0 && eta && etd) {
    try {
      const etdDate = new Date(etd);
      const etaDate = new Date(eta);
      const days = Math.max(1, Math.ceil((etaDate.getTime() - etdDate.getTime()) / (1000 * 60 * 60 * 24)));
      transitTimeDays = days;
    } catch (e) {
      // Invalid dates, use default
      transitTimeDays = transportMode === 'AIR' ? 3 : 7;
    }
  }
  
  // Extract seller info (handle both object and flat structure)
  const sellerData = (formData.seller || {}) as Record<string, unknown>;
  const seller: Party = {
    name: sellerData.name ? String(sellerData.name) : undefined,
    company: String(sellerData.company || sellerData.companyName || sellerData.company_name || ''),
    email: String(sellerData.email || ''),
    phone: String(sellerData.phone || ''),
    country: sellerData.country ? (typeof sellerData.country === 'string' ? sellerData.country : String((sellerData.country as Record<string, unknown>).name || '')) : '',
    city: sellerData.city ? String(sellerData.city) : undefined,
    address: sellerData.address ? String(sellerData.address) : undefined,
    tax_id: sellerData.tax_id || sellerData.taxId ? String(sellerData.tax_id || sellerData.taxId) : undefined,
  };
  
  // Extract buyer info
  const buyerData = (formData.buyer || {}) as Record<string, unknown>;
  const buyer: Party = {
    name: buyerData.name ? String(buyerData.name) : undefined,
    company: String(buyerData.company || buyerData.companyName || buyerData.company_name || ''),
    email: String(buyerData.email || ''),
    phone: String(buyerData.phone || ''),
    country: buyerData.country ? (typeof buyerData.country === 'string' ? buyerData.country : String((buyerData.country as Record<string, unknown>).name || '')) : '',
    city: buyerData.city ? String(buyerData.city) : undefined,
    address: buyerData.address ? String(buyerData.address) : undefined,
    tax_id: buyerData.tax_id || buyerData.taxId ? String(buyerData.tax_id || buyerData.taxId) : undefined,
  };
  
  // Extract cargo info
  const cargoData = (formData.cargo || {}) as Record<string, unknown>;
  
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
    containerType: String(formData.container || formData.container_type || (transportMode === 'AIR' ? 'Air Cargo Unit' : '40HC')),
    serviceRoute: formData.service_route || formData.serviceRoute ? String(formData.service_route || formData.serviceRoute) : undefined,
    carrier: formData.carrier ? String(formData.carrier) : undefined,
    
    etd,
    eta,
    transitTimeDays,
    
    cargoType: String(cargoData.cargo_type || cargoData.cargoType || formData.cargo_type || 'Electronics'),
    cargoCategory: cargoData.cargo_category || cargoData.cargoCategory ? String(cargoData.cargo_category || cargoData.cargoCategory) : undefined,
    hsCode: cargoData.hs_code || cargoData.hsCode ? String(cargoData.hs_code || cargoData.hsCode) : undefined,
    packaging: cargoData.packaging || cargoData.packing_type ? String(cargoData.packaging || cargoData.packing_type) : undefined,
    packages: Number(cargoData.packages || cargoData.numberOfPackages || cargoData.packageCount) || 1,
    grossWeightKg: cargoData.gross_weight_kg || cargoData.grossWeight ? Number(cargoData.gross_weight_kg || cargoData.grossWeight) : undefined,
    netWeightKg: cargoData.net_weight_kg || cargoData.netWeight ? Number(cargoData.net_weight_kg || cargoData.netWeight) : undefined,
    volumeCbm: cargoData.volume_cbm || cargoData.volume || cargoData.volumeM3 ? Number(cargoData.volume_cbm || cargoData.volume || cargoData.volumeM3) : undefined,
    
    cargoValue,
    currency: (formData.currency === 'VND' ? 'VND' : 'USD') as 'USD' | 'VND',
    
    incoterm: formData.incoterm ? String(formData.incoterm) : undefined,
    incotermLocation: formData.incoterm_location || formData.incotermLocation ? String(formData.incoterm_location || formData.incotermLocation) : undefined,
    priority,
    
    seller,
    buyer,
    forwarder: formData.forwarder ? (formData.forwarder as Partial<Party>) : undefined,
    
    modules: {
      esg: modulesData.esg !== false,
      weather: modulesData.weather !== false,
      portCongestion: modulesData.portCongestion !== false && modulesData.port !== false,
      carrierPerformance: modulesData.carrierPerformance !== false && modulesData.carrier !== false,
      marketScanner: modulesData.marketScanner === true || modulesData.market === true,
      insurance: modulesData.insurance !== false,
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
      eta: domainCase.eta || '',
      transit_time_days: domainCase.transitTimeDays,
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
      packages: domainCase.packages,
      gross_weight_kg: domainCase.grossWeightKg || 0,
      net_weight_kg: domainCase.netWeightKg || 0,
      volume_cbm: domainCase.volumeCbm || 0,
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
    value: domainCase.cargoValue,
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
    try {
      // If already ISO format, return as is
      if (dateStr.includes('T')) return dateStr;
      // If YYYY-MM-DD, convert to ISO
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
    pol: {
      code: domainCase.pol,
      name: polInfo.name,
    },
    pod: {
      code: domainCase.pod,
      name: podInfo.name,
    },
    carrier: domainCase.carrier || '',
    etd: normalizeDate(domainCase.etd),
    eta: normalizeDate(domainCase.eta),
    transitTime: domainCase.transitTimeDays,
    container: domainCase.containerType,
    cargo: domainCase.cargoType,
    cargoType: domainCase.cargoType,
    containerType: domainCase.containerType,
    packaging: domainCase.packaging || null,
    incoterm: domainCase.incoterm || '',
    cargoValue: domainCase.cargoValue,
  };
}
