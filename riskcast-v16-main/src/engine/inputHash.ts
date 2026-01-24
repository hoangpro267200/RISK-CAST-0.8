/**
 * Input Hash Utility
 * 
 * Generates deterministic hash of analysis input for stale result detection.
 * Used to ensure Results page only displays data from the current analysis run.
 */

import type { DomainCase } from '@/domain/case.schema';

/**
 * Compute deterministic hash of canonical analysis input
 * 
 * This hash should be:
 * - Deterministic (same input = same hash)
 * - Include all fields that affect analysis results
 * - Exclude fields that don't affect results (timestamps, UI state, etc.)
 * 
 * @param domainCase - Canonical domain case
 * @returns SHA-256 hash as hex string (or simple hash if crypto not available)
 */
export function computeInputHash(domainCase: DomainCase): string {
  // Extract canonical fields that affect analysis
  const canonicalPayload = {
    // Trade route
    pol: domainCase.pol,
    pod: domainCase.pod,
    mode: domainCase.transportMode,
    carrier: domainCase.carrier || '',
    etd: domainCase.etd,
    eta: domainCase.eta || '',
    transit_time_days: domainCase.transitTimeDays,
    container_type: domainCase.containerType,
    incoterm: domainCase.incoterm || '',
    
    // Cargo
    cargo_type: domainCase.cargoType,
    hs_code: domainCase.hsCode || '',
    packages: domainCase.packages,
    gross_weight_kg: domainCase.grossWeightKg || 0,
    volume_cbm: domainCase.volumeCbm || 0,
    packing_type: domainCase.packaging || '',
    stackability: '',
    temp_control_required: false,
    is_dg: false,
    
    // Value
    value: domainCase.cargoValue,
    currency: domainCase.currency,
  };
  
  // Create deterministic string representation
  const payloadStr = JSON.stringify(canonicalPayload, Object.keys(canonicalPayload).sort());
  
  // Use Web Crypto API if available (browser), otherwise simple hash
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    // For browser: use async hashing (we'll need to make this async or use sync alternative)
    // For now, use a simple synchronous hash
    return simpleHash(payloadStr);
  } else {
    // Fallback: simple hash
    return simpleHash(payloadStr);
  }
}

/**
 * Simple deterministic hash function (FNV-1a variant)
 * Not cryptographically secure, but sufficient for input matching
 */
function simpleHash(str: string): string {
  let hash = 2166136261; // FNV offset basis
  for (let i = 0; i < str.length; i++) {
    hash ^= str.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return Math.abs(hash).toString(36);
}

/**
 * Async version using Web Crypto API (more secure)
 */
export async function computeInputHashAsync(domainCase: DomainCase): Promise<string> {
  const canonicalPayload = {
    pol: domainCase.pol,
    pod: domainCase.pod,
    mode: domainCase.transportMode,
    carrier: domainCase.carrier || '',
    etd: domainCase.etd,
    eta: domainCase.eta || '',
    transit_time_days: domainCase.transitTimeDays,
    container_type: domainCase.containerType,
    incoterm: domainCase.incoterm || '',
    cargo_type: domainCase.cargoType,
    hs_code: domainCase.hsCode || '',
    packages: domainCase.packages,
    gross_weight_kg: domainCase.grossWeightKg || 0,
    volume_cbm: domainCase.volumeCbm || 0,
    packing_type: domainCase.packaging || '',
    stackability: '',
    temp_control_required: false,
    is_dg: false,
    value: domainCase.cargoValue,
    currency: domainCase.currency,
  };
  
  const payloadStr = JSON.stringify(canonicalPayload, Object.keys(canonicalPayload).sort());
  
  if (typeof crypto !== 'undefined' && crypto.subtle) {
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(payloadStr);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('').substring(0, 16);
    } catch (e) {
      console.warn('[computeInputHashAsync] Crypto API failed, using simple hash:', e);
      return simpleHash(payloadStr);
    }
  }
  
  return simpleHash(payloadStr);
}
