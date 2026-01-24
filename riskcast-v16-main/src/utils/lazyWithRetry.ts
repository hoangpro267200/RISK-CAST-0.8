/**
 * Lazy loading with retry logic
 * 
 * Handles network errors (ERR_NETWORK_CHANGED, Failed to fetch) by retrying
 * the import up to 3 times with exponential backoff.
 */

import React from 'react';

/**
 * Retry a promise-returning function with exponential backoff
 */
async function retry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error: any) {
      lastError = error;
      
      // Check if it's a network error
      const isNetworkError = 
        error?.message?.includes('Failed to fetch') ||
        error?.message?.includes('Failed to fetch dynamically imported module') ||
        error?.message?.includes('NetworkError') ||
        error?.message?.includes('ERR_NETWORK_CHANGED') ||
        error?.name === 'TypeError' ||
        error?.code === 'ERR_NETWORK_CHANGED' ||
        error?.code === 'ERR_INTERNET_DISCONNECTED' ||
        error?.code === 'ERR_CONNECTION_REFUSED' ||
        error?.code === 'ERR_CONNECTION_RESET';
      
      // Only retry network errors
      if (!isNetworkError) {
        // Not a network error, throw immediately
        throw error;
      }
      
      // Last attempt, throw the error
      if (attempt === maxRetries - 1) {
        // Mark as network error for error boundary handling
        const networkError = new Error(
          `Failed to load module after ${maxRetries} attempts: ${error.message}`
        );
        (networkError as any).isNetworkError = true;
        (networkError as any).originalError = error;
        throw networkError;
      }
      
      // Exponential backoff: 1s, 2s, 4s
      const backoffDelay = delay * Math.pow(2, attempt);
      
      // Only log retry attempts in development if explicitly enabled
      // This prevents console spam during normal development
      if (import.meta.env.MODE === 'development' && import.meta.env.VITE_DEBUG_LAZY_LOAD === 'true') {
        console.debug(
          `[LazyLoad] Retrying module import (attempt ${attempt + 1}/${maxRetries}) after ${backoffDelay}ms...`
        );
      }
      
      await new Promise(resolve => setTimeout(resolve, backoffDelay));
    }
  }
  
  throw lastError || new Error('Failed after retries');
}

/**
 * Create a lazy-loaded component with retry logic for network errors
 * 
 * @param importFn - Function that returns a promise for the module
 * @param maxRetries - Maximum number of retry attempts (default: 3)
 * @returns Lazy component that retries on network errors
 */
export function lazyWithRetry<T extends React.ComponentType<any>>(
  importFn: () => Promise<{ default: T }>,
  maxRetries: number = 3
): React.LazyExoticComponent<T> {
  return React.lazy(() => retry(importFn, maxRetries));
}
