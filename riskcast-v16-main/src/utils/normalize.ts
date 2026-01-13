/**
 * Normalization utilities for engine data adapter
 * 
 * These functions provide safe, deterministic conversion of raw engine output
 * to normalized values with consistent scales and types.
 */

/**
 * Convert unknown value to number with fallback
 * Handles string numbers, null, undefined, and invalid values safely
 */
export function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : fallback;
  }
  if (typeof value === 'string') {
    const parsed = Number.parseFloat(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  return fallback;
}

/**
 * Clamp number to [min, max] range
 * Returns fallback if value is not finite
 */
export function clamp(num: number, min: number, max: number): number {
  if (!Number.isFinite(num)) {
    return min;
  }
  return Math.min(max, Math.max(min, num));
}

/**
 * Convert value to percentage (0-100)
 * 
 * Handles both 0-1 scale and 0-100 scale:
 * - If value > 1 and <= 100, assume already in 0-100 scale
 * - If value <= 1, assume 0-1 scale and multiply by 100
 * - Clamps to [0, 100]
 */
export function toPercent(value: unknown): number {
  const num = toNumber(value, 0);
  
  // If value is already in 0-100 range, return as-is (clamped)
  if (num > 1 && num <= 100) {
    return clamp(num, 0, 100);
  }
  
  // Otherwise, assume 0-1 scale and convert
  const normalized = num * 100;
  return clamp(normalized, 0, 100);
}

/**
 * Round number to specified decimal places
 * Returns 0 if value is not finite
 */
export function round(num: number, decimals: number): number {
  if (!Number.isFinite(num)) {
    return 0;
  }
  const factor = 10 ** decimals;
  return Math.round(num * factor) / factor;
}

/**
 * Validate ISO date string
 * Returns true if string is a valid ISO date format
 */
export function isValidISODate(str: unknown): boolean {
  if (typeof str !== 'string' || str.trim() === '') {
    return false;
  }
  
  // Try parsing as ISO date
  const date = new Date(str);
  
  // Check if date is valid and string matches ISO format
  if (!Number.isFinite(date.getTime())) {
    return false;
  }
  
  // Basic ISO format check (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss)
  const isoPattern = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[+-]\d{2}:\d{2})?)?$/;
  return isoPattern.test(str.trim());
}

/**
 * Convert string to URL-friendly slug
 * Used for generating stable IDs from titles
 */
export function slugify(str: unknown): string {
  if (typeof str !== 'string') {
    return '';
  }
  
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '') // Remove special characters
    .replace(/[\s_-]+/g, '-') // Replace spaces/underscores with hyphens
    .replace(/^-+|-+$/g, ''); // Remove leading/trailing hyphens
}

/**
 * Safe string conversion with fallback
 */
export function toString(value: unknown, fallback = ''): string {
  if (typeof value === 'string') {
    return value;
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  return String(value);
}

/**
 * Safe array conversion with fallback
 */
export function toArray<T>(value: unknown, fallback: T[] = []): T[] {
  return Array.isArray(value) ? (value as T[]) : fallback;
}

/**
 * Normalize risk level string to canonical RiskLevel type
 */
export function normalizeRiskLevel(level: unknown): 'Low' | 'Medium' | 'High' | 'Critical' | 'Unknown' {
  const str = toString(level).trim();
  const normalized = str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
  
  if (normalized === 'Low' || normalized === 'Medium' || normalized === 'High' || normalized === 'Critical') {
    return normalized;
  }
  
  return 'Unknown';
}

