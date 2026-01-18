/**
 * Domain Case Schema - Single Source of Truth for all pages
 * 
 * This schema defines the canonical data structure for a risk analysis case.
 * All transforms (Input → Summary → Results) must use this as the contract.
 * 
 * ARCHITECTURE:
 * - Input form state → DomainCase (via mapInputFormToDomainCase)
 * - DomainCase → ShipmentData (via mapDomainCaseToShipmentData)
 * - DomainCase → ShipmentViewModel (via mapDomainCaseToShipmentViewModel)
 * - All pages use DomainCase as the source of truth
 */

/**
 * Port code type (3-10 characters)
 */
export type PortCode = string; // e.g., 'SGN', 'LAX', 'VNSGN'

/**
 * Transport mode enum
 */
export type TransportMode = 'AIR' | 'SEA' | 'ROAD' | 'RAIL' | 'MULTIMODAL';

/**
 * Priority level
 */
export type Priority = 'normal' | 'express' | 'urgent';

/**
 * Currency
 */
export type Currency = 'USD' | 'VND';

/**
 * Party information (seller, buyer, forwarder)
 */
export interface Party {
  name?: string;
  company: string;  // Required
  email: string;    // Required, validated
  phone: string;    // Required
  country: string;  // Required
  city?: string;
  address?: string;
  tax_id?: string;
}

/**
 * Algorithm modules configuration
 */
export interface ModulesState {
  esg: boolean;
  weather: boolean;
  portCongestion: boolean;
  carrierPerformance: boolean;
  marketScanner: boolean;
  insurance: boolean;
}

/**
 * Domain Case - The canonical data structure for a risk analysis case
 * 
 * This is the SINGLE SOURCE OF TRUTH for all pages.
 * All field names are normalized (camelCase).
 * All values have sensible defaults.
 */
export interface DomainCase {
  // Metadata
  caseId: string;           // Unique case identifier (e.g., "CASE-1705123456789")
  runId?: string;           // Run/analysis identifier (optional, generated on analysis)
  version: string;          // Schema version (default: "1.0")
  createdAt: string;        // ISO datetime string
  lastModified: string;     // ISO datetime string
  
  // Route & Transport
  pol: PortCode;                    // Port of Loading (required)
  pod: PortCode;                    // Port of Discharge (required)
  transportMode: TransportMode;     // Mode of transport (required)
  containerType: string;            // Container type (required, e.g., "40HC", "20RF")
  serviceRoute?: string;            // Service route name (optional)
  carrier?: string;                 // Carrier name (optional)
  
  // Dates & Transit
  etd: string;                      // Estimated Time of Departure (ISO date string or YYYY-MM-DD)
  eta?: string;                     // Estimated Time of Arrival (ISO date string or YYYY-MM-DD, optional)
  transitTimeDays: number;          // Transit time in days (required, >= 0)
  
  // Cargo
  cargoType: string;                // Cargo type (required, e.g., "Electronics", "Perishable")
  cargoCategory?: string;           // Cargo category (optional, e.g., "General", "Fragile")
  hsCode?: string;                  // HS Code (optional, 6-10 digits)
  packaging?: string;               // Packaging type (optional, e.g., "Pallets", "Boxes")
  packages: number;                 // Number of packages (required, >= 1)
  grossWeightKg?: number;           // Gross weight in kg (optional, >= 0)
  netWeightKg?: number;             // Net weight in kg (optional, >= 0, <= grossWeightKg)
  volumeCbm?: number;               // Volume in CBM (optional, >= 0)
  
  // Value
  cargoValue: number;               // Cargo value (required, >= 0)
  currency: Currency;               // Currency (default: "USD")
  
  // Terms
  incoterm?: string;                // Incoterm (optional, e.g., "FOB", "CIF")
  incotermLocation?: string;        // Incoterm location (optional, required for some incoterms)
  priority: Priority;               // Priority level (default: "normal")
  
  // Parties
  seller: Party;                    // Seller information (required)
  buyer: Party;                     // Buyer information (required)
  forwarder?: Partial<Party>;       // Forwarder information (optional)
  
  // Modules (for analysis)
  modules: ModulesState;            // Algorithm modules configuration
}

/**
 * Default modules state
 */
export const DEFAULT_MODULES: ModulesState = {
  esg: true,
  weather: true,
  portCongestion: true,
  carrierPerformance: true,
  marketScanner: false,
  insurance: true,
};

/**
 * Create a new DomainCase with defaults
 */
export function createDefaultDomainCase(): DomainCase {
  const now = new Date().toISOString();
  const caseId = `CASE-${Date.now()}`;
  
  return {
    caseId,
    version: '1.0',
    createdAt: now,
    lastModified: now,
    
    // Route & Transport (defaults)
    pol: 'SGN',
    pod: 'LAX',
    transportMode: 'AIR',
    containerType: 'Air Cargo Unit',
    transitTimeDays: 3,
    
    // Dates (defaults: 7 days from now for ETD)
    etd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]!,
    
    // Cargo (defaults)
    cargoType: 'Electronics',
    packages: 1,
    cargoValue: 0,
    currency: 'USD',
    
    // Priority
    priority: 'normal',
    
    // Parties (empty but valid)
    seller: {
      company: '',
      email: '',
      phone: '',
      country: '',
    },
    buyer: {
      company: '',
      email: '',
      phone: '',
      country: '',
    },
    
    // Modules
    modules: { ...DEFAULT_MODULES },
  };
}

/**
 * Helper: Normalize transport mode string to TransportMode enum
 */
export function normalizeTransportMode(mode: string | null | undefined): TransportMode {
  if (!mode) return 'AIR';
  const normalized = mode.toUpperCase().trim();
  
  // Handle common variations
  if (normalized.includes('AIR') || normalized === 'A') return 'AIR';
  if (normalized.includes('SEA') || normalized === 'OCEAN' || normalized.includes('FCL') || normalized.includes('LCL')) return 'SEA';
  if (normalized.includes('ROAD') || normalized === 'TRUCK') return 'ROAD';
  if (normalized.includes('RAIL')) return 'RAIL';
  if (normalized.includes('MULTI')) return 'MULTIMODAL';
  
  // Default
  return 'AIR';
}

/**
 * Helper: Normalize priority string to Priority enum
 */
export function normalizePriority(priority: string | null | undefined): Priority {
  if (!priority) return 'normal';
  const normalized = priority.toLowerCase().trim();
  
  if (normalized === 'express' || normalized === 'fast') return 'express';
  if (normalized === 'urgent' || normalized === 'rush') return 'urgent';
  
  return 'normal';
}
