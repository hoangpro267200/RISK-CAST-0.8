/**
 * Frontend Auth Configuration
 * 
 * RISKCAST Auth System - Phase 4
 * Client-side auth configuration (reads from backend or defaults).
 */

// Check if auth is enabled (default: true for frontend, backend controls actual behavior)
// In production, this could be fetched from an API endpoint
export const AUTH_CONFIG = {
  // These should match backend config
  // Frontend will respect backend's AUTH_ENABLED setting via API responses
  ENABLED: true, // Default to true, backend will enforce
  PROTECT_INPUT: false, // Can be overridden by backend
  PROTECT_RESULTS: false, // Can be overridden by backend
};

/**
 * Check if a route should be protected
 */
export function shouldProtectRoute(routePath: string): boolean {
  if (!AUTH_CONFIG.ENABLED) {
    return false;
  }

  // Always protect account surfaces
  if (routePath === '/overview' || routePath.startsWith('/overview') || routePath === '/account' || routePath.startsWith('/account')) {
    return true;
  }

  if (routePath.includes('/input') && AUTH_CONFIG.PROTECT_INPUT) {
    return true;
  }

  if (routePath === '/results' && AUTH_CONFIG.PROTECT_RESULTS) {
    return true;
  }

  return false;
}
