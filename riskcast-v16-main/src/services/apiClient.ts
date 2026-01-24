/**
 * API Client with Observability (Phase 5)
 * 
 * Features:
 * - Correlation ID generation and propagation
 * - Request/response logging (dev mode)
 * - Error classification and handling
 * - Retry logic with exponential backoff
 */

// ============================================================================
// CORRELATION ID MANAGEMENT
// ============================================================================

/**
 * Generate a unique correlation ID for request tracing
 */
export function generateCorrelationId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `rc-${timestamp}-${random}`;
}

/**
 * Get or create a correlation ID for the current request context
 * Persists across the page session
 */
let sessionCorrelationId: string | null = null;

export function getSessionCorrelationId(): string {
  if (!sessionCorrelationId) {
    sessionCorrelationId = generateCorrelationId();
  }
  return sessionCorrelationId;
}

/**
 * Reset session correlation ID (e.g., after navigation)
 */
export function resetSessionCorrelationId(): void {
  sessionCorrelationId = generateCorrelationId();
}

// ============================================================================
// REQUEST CLASSIFICATION
// ============================================================================

export type RequestErrorType = 
  | 'network'      // Connection failed
  | 'timeout'      // Request timed out
  | 'auth'         // 401/403 errors
  | 'validation'   // 400/422 errors
  | 'server'       // 5xx errors
  | 'not_found'    // 404 errors
  | 'unknown';     // Other errors

export interface ClassifiedError {
  type: RequestErrorType;
  message: string;
  status?: number;
  correlationId: string;
  shouldRetry: boolean;
  userMessage: string;
}

/**
 * Classify an error for proper handling
 */
export function classifyError(error: unknown, correlationId: string): ClassifiedError {
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      type: 'network',
      message: error.message,
      correlationId,
      shouldRetry: true,
      userMessage: 'Network connection failed. Please check your internet connection.',
    };
  }
  
  if (error instanceof DOMException && error.name === 'AbortError') {
    return {
      type: 'timeout',
      message: 'Request timed out',
      correlationId,
      shouldRetry: true,
      userMessage: 'Request timed out. Please try again.',
    };
  }
  
  if (error instanceof Response || (error && typeof error === 'object' && 'status' in error)) {
    const status = (error as any).status as number;
    
    if (status === 401 || status === 403) {
      return {
        type: 'auth',
        message: `Authentication error: ${status}`,
        status,
        correlationId,
        shouldRetry: false,
        userMessage: status === 401 
          ? 'Please log in to continue.' 
          : 'You do not have permission to perform this action.',
      };
    }
    
    if (status === 404) {
      return {
        type: 'not_found',
        message: 'Resource not found',
        status,
        correlationId,
        shouldRetry: false,
        userMessage: 'The requested resource was not found.',
      };
    }
    
    if (status === 400 || status === 422) {
      return {
        type: 'validation',
        message: `Validation error: ${status}`,
        status,
        correlationId,
        shouldRetry: false,
        userMessage: 'The request contained invalid data. Please check your input.',
      };
    }
    
    if (status >= 500) {
      return {
        type: 'server',
        message: `Server error: ${status}`,
        status,
        correlationId,
        shouldRetry: true,
        userMessage: 'A server error occurred. Please try again later.',
      };
    }
  }
  
  return {
    type: 'unknown',
    message: error instanceof Error ? error.message : String(error),
    correlationId,
    shouldRetry: false,
    userMessage: 'An unexpected error occurred.',
  };
}

// ============================================================================
// API CLIENT
// ============================================================================

export interface ApiRequestOptions extends RequestInit {
  /** Timeout in milliseconds (default: 30000) */
  timeout?: number;
  /** Number of retry attempts (default: 0) */
  retries?: number;
  /** Custom correlation ID (auto-generated if not provided) */
  correlationId?: string;
  /** Skip adding correlation headers */
  skipCorrelation?: boolean;
}

export interface ApiResponse<T = unknown> {
  data: T | null;
  error: ClassifiedError | null;
  status: number;
  correlationId: string;
  duration: number;
}

/**
 * Make an API request with observability features
 */
export async function apiRequest<T = unknown>(
  url: string,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> {
  const {
    timeout = 30000,
    retries = 0,
    correlationId = generateCorrelationId(),
    skipCorrelation = false,
    ...fetchOptions
  } = options;
  
  const startTime = performance.now();
  
  // Add correlation headers
  const headers = new Headers(fetchOptions.headers);
  if (!skipCorrelation) {
    headers.set('X-Correlation-ID', correlationId);
    headers.set('X-Session-ID', getSessionCorrelationId());
  }
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  let lastError: ClassifiedError | null = null;
  let attempt = 0;
  
  while (attempt <= retries) {
    try {
      if (import.meta.env.DEV) {
        console.log(`[API] ${fetchOptions.method || 'GET'} ${url} (attempt ${attempt + 1}/${retries + 1}, cid: ${correlationId})`);
      }
      
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);
      const duration = performance.now() - startTime;
      
      // Check for error responses
      if (!response.ok) {
        const error = classifyError(response, correlationId);
        
        if (import.meta.env.DEV) {
          console.warn(`[API] Error ${response.status} for ${url} (${duration.toFixed(0)}ms, cid: ${correlationId})`);
        }
        
        // Retry server errors
        if (error.shouldRetry && attempt < retries) {
          lastError = error;
          attempt++;
          // Exponential backoff: 1s, 2s, 4s...
          await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
          continue;
        }
        
        return {
          data: null,
          error,
          status: response.status,
          correlationId,
          duration,
        };
      }
      
      // Parse response
      let data: T | null = null;
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        data = await response.json() as T;
      }
      
      if (import.meta.env.DEV) {
        console.log(`[API] Success ${response.status} for ${url} (${duration.toFixed(0)}ms, cid: ${correlationId})`);
      }
      
      return {
        data,
        error: null,
        status: response.status,
        correlationId,
        duration,
      };
      
    } catch (err) {
      clearTimeout(timeoutId);
      const duration = performance.now() - startTime;
      const error = classifyError(err, correlationId);
      
      if (import.meta.env.DEV) {
        console.warn(`[API] ${error.type} error for ${url} (${duration.toFixed(0)}ms, cid: ${correlationId}):`, error.message);
      }
      
      // Retry network/timeout errors
      if (error.shouldRetry && attempt < retries) {
        lastError = error;
        attempt++;
        await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 1000));
        continue;
      }
      
      return {
        data: null,
        error,
        status: 0,
        correlationId,
        duration,
      };
    }
  }
  
  // Should not reach here, but return last error if we do
  const duration = performance.now() - startTime;
  return {
    data: null,
    error: lastError || classifyError(new Error('Max retries exceeded'), correlationId),
    status: 0,
    correlationId,
    duration,
  };
}

// ============================================================================
// CONVENIENCE METHODS
// ============================================================================

export const api = {
  get: <T = unknown>(url: string, options?: Omit<ApiRequestOptions, 'method' | 'body'>) =>
    apiRequest<T>(url, { ...options, method: 'GET' }),
  
  post: <T = unknown>(url: string, data?: unknown, options?: Omit<ApiRequestOptions, 'method'>) =>
    apiRequest<T>(url, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers as Record<string, string>),
      },
    }),
  
  put: <T = unknown>(url: string, data?: unknown, options?: Omit<ApiRequestOptions, 'method'>) =>
    apiRequest<T>(url, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers as Record<string, string>),
      },
    }),
  
  delete: <T = unknown>(url: string, options?: Omit<ApiRequestOptions, 'method'>) =>
    apiRequest<T>(url, { ...options, method: 'DELETE' }),
};

export default api;
