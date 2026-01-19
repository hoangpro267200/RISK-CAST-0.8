/**
 * Summary Export Module
 * 
 * Exports canonical shipmentSummaryState from Summary page.
 * Persists to sessionStorage (primary) and localStorage (fallback).
 * 
 * @file summary_export.js
 */

const SUMMARY_STATE_KEY = 'RISKCAST_SUMMARY_STATE';
const SUMMARY_VERSION = '1.0.0';

/**
 * Create canonical shipmentSummaryState from summary page data
 * @param {Object} summaryData - Raw summary data from page
 * @returns {Object} Canonical shipmentSummaryState
 */
export function createSummaryState(summaryData = {}) {
  const timestamp = new Date().toISOString();
  
  // Extract shipment metadata
  const shipment = summaryData.shipment || {};
  const route = summaryData.route || shipment.route || '';
  const transportMode = summaryData.transportMode || shipment.transport_mode || shipment.mode || '';
  const cargoType = summaryData.cargoType || shipment.cargo_type || '';
  const container = summaryData.container || shipment.container || shipment.container_type || '';
  const incoterm = summaryData.incoterm || shipment.incoterm || '';
  const cargoValue = parseFloat(summaryData.cargoValue || shipment.cargo_value || shipment.value_usd || 0);
  const etd = summaryData.etd || shipment.etd || '';
  const eta = summaryData.eta || shipment.eta || '';
  const transitTime = summaryData.transitTime || shipment.transit_time || shipment.transit_time_days || 0;
  const distance = summaryData.distance || shipment.distance || 0;
  
  // Extract risk modules (selected modules)
  const riskModules = summaryData.riskModules || {
    esg: false,
    weather: false,
    congestion: false,
    carrier_perf: false,
    market: false,
    insurance: false
  };
  
  // Extract normalized risk inputs (per layer)
  const riskInputs = summaryData.riskInputs || {
    portCongestion: null,
    weatherVolatility: null,
    carrierReliability: null,
    geopolitical: null,
    financial: null,
    esg: null
  };
  
  // Generate shipment ID if not present
  const shipmentId = summaryData.shipmentId || shipment.id || `SH-${new Date().getFullYear()}-${Math.abs(hashCode(route + timestamp)) % 10000}`;
  
  return {
    version: SUMMARY_VERSION,
    timestamp: timestamp,
    shipmentId: shipmentId,
    shipment: {
      id: shipmentId,
      route: route,
      transportMode: transportMode,
      cargoType: cargoType,
      container: container,
      incoterm: incoterm,
      cargoValue: cargoValue,
      etd: etd,
      eta: eta,
      transitTime: transitTime,
      distance: distance,
      // Additional metadata
      origin: summaryData.origin || shipment.origin || extractOrigin(route),
      destination: summaryData.destination || shipment.destination || extractDestination(route),
      carrier: summaryData.carrier || shipment.carrier || '',
      packaging: summaryData.packaging || shipment.packaging || '',
      weight: summaryData.weight || shipment.weight || shipment.gross_weight_kg || null,
      volume: summaryData.volume || shipment.volume || shipment.volume_cbm || null
    },
    riskModules: riskModules,
    riskInputs: riskInputs,
    // Traceability metadata
    source: 'summary_page',
    validated: false // Will be validated by ResultsOS
  };
}

/**
 * Persist summary state to storage
 * @param {Object} summaryState - Canonical shipmentSummaryState
 */
export function persistSummaryState(summaryState) {
  try {
    const serialized = JSON.stringify(summaryState);
    
    // Primary: sessionStorage (fast navigation)
    if (typeof sessionStorage !== 'undefined') {
      sessionStorage.setItem(SUMMARY_STATE_KEY, serialized);
    }
    
    // Fallback: localStorage (reload/crash recovery)
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(SUMMARY_STATE_KEY, serialized);
    }
  } catch (error) {
    console.error('SummaryExport: Failed to persist state', error);
  }
}

/**
 * Export summary state (create + persist)
 * @param {Object} summaryData - Raw summary data
 */
export function exportSummaryState(summaryData) {
  const state = createSummaryState(summaryData);
  persistSummaryState(state);
  return state;
}

// Expose to window for non-module scripts
if (typeof window !== 'undefined') {
  window.exportSummaryState = exportSummaryState;
}

/**
 * Helper: Extract origin from route string
 * @param {string} route - Route string (e.g., "Shanghai → Los Angeles")
 * @returns {string} Origin
 */
function extractOrigin(route) {
  if (!route) return '';
  const parts = route.split('→');
  return parts[0] ? parts[0].trim() : '';
}

/**
 * Helper: Extract destination from route string
 * @param {string} route - Route string
 * @returns {string} Destination
 */
function extractDestination(route) {
  if (!route) return '';
  const parts = route.split('→');
  if (parts.length > 1) {
    return parts[parts.length - 1].trim();
  }
  return '';
}

/**
 * Helper: Simple hash code for ID generation
 * @param {string} str - Input string
 * @returns {number} Hash code
 */
function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return hash;
}
