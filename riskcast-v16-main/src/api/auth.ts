/**
 * Authentication & Account API Client
 */

import { z } from 'zod';

export interface User {
  id: number;
  email: string;
  name: string | null;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}

export interface Session {
  id: number;
  user_id: number;
  expires_at: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  is_valid: boolean;
}

export interface SignupRequest {
  email: string;
  password: string;
  name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

/**
 * API response wrapper
 */
interface ApiResponse<T> {
  success?: boolean;
  data?: T;
  message?: string;
  detail?: string;
}

const UserSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  name: z.string().nullable(),
  is_active: z.boolean(),
  email_verified: z.boolean(),
  created_at: z.string(),
});

const SessionSchema = z.object({
  id: z.number(),
  user_id: z.number(),
  expires_at: z.string(),
  user_agent: z.string().nullable(),
  ip_address: z.string().nullable(),
  created_at: z.string(),
  is_valid: z.boolean(),
});

const PreferenceSchema = z.object({
  timezone: z.string().nullable().optional(),
  currency: z.string().nullable().optional(),
  units: z.string().nullable().optional(),
  theme: z.string().nullable().optional(),
  personalization_opt_in: z.boolean().optional(),
  preferences_json: z.record(z.string(), z.any()).nullable().optional(),
});

const AccountSchema = UserSchema.extend({
  preferences: PreferenceSchema,
});

function parseWithSchema<T>(schema: z.ZodSchema<T>, value: unknown): T {
  return schema.parse(value);
}

function getCookieValue(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  const value = match && match[2] ? match[2] : null;
  return value ? decodeURIComponent(value) : null;
}

async function ensureCsrfToken(): Promise<string | null> {
  const existing = getCookieValue('csrf_token');
  if (existing) return existing;
  try {
    const resp = await fetch('/api/auth/csrf', { credentials: 'include' });
    const data = await resp.json();
    if (data?.csrf_token) {
      return data.csrf_token;
    }
  } catch {
    // ignore
  }
  return getCookieValue('csrf_token');
}

/**
 * Make authenticated API request
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  let response: Response;
  const method = (options.method || 'GET').toUpperCase();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrfToken = await ensureCsrfToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }
  
  try {
    response = await fetch(`/api/auth${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Include cookies
    });
  } catch (fetchError: any) {
    // Handle network errors (ERR_NETWORK_CHANGED, ERR_INTERNET_DISCONNECTED, etc.)
    const isNetworkError = 
      fetchError?.message?.includes('Failed to fetch') ||
      fetchError?.message?.includes('NetworkError') ||
      fetchError?.name === 'TypeError' ||
      fetchError?.code === 'ERR_NETWORK_CHANGED' ||
      fetchError?.code === 'ERR_INTERNET_DISCONNECTED';
    
    if (isNetworkError) {
      const networkError = new Error('Network error: Unable to connect to server');
      (networkError as any).status = 0;
      (networkError as any).isNetworkError = true;
      throw networkError;
    }
    
    // Re-throw other errors
    throw fetchError;
  }

  // Handle redirects (e.g., 401 → login page)
  if (response.redirected) {
    const error = new Error('Unauthorized');
    (error as any).status = 401;
    throw error;
  }

  // For 401 responses, handle gracefully before JSON parsing
  // Note: Browser will still log network errors in console, but we handle them silently
  if (response.status === 401) {
    const error = new Error('Not authenticated');
    (error as any).status = 401;
    (error as any).isAuthError = true; // Mark as auth error for silent handling
    throw error;
  }

  let data: ApiResponse<T> | T;
  try {
    data = await response.json();
  } catch (parseError) {
    const error = new Error('Invalid response format');
    (error as any).status = response.status;
    throw error;
  }

  // Envelope handling
  if (typeof data === 'object' && data !== null && 'success' in data) {
    const wrapped = data as ApiResponse<T> & { error?: { code?: string; message?: string; details?: unknown } };
    if (!wrapped.success) {
      const error = new Error(wrapped.detail || wrapped.message || wrapped.error?.message || 'Request failed');
      (error as any).status = response.status;
      (error as any).code = wrapped.error?.code || (wrapped as any).error_code;
      throw error;
    }
    return (wrapped.data || wrapped) as T;
  }

  if (!response.ok) {
    const errorData = data as any;
    const err = new Error(errorData?.error?.message || errorData?.message || 'Request failed');
    (err as any).status = response.status;
    (err as any).code = errorData?.error?.code;
    (err as any).details = errorData?.error?.details;
    throw err;
  }

  return data as T;
}

async function accountRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  let response: Response;
  const method = (options.method || 'GET').toUpperCase();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrfToken = await ensureCsrfToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }

  response = await fetch(`/api/account${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (response.status === 401) {
    throw new Error('Not authenticated');
  }
  const json = await response.json();
  if (json && typeof json === 'object' && 'success' in json) {
    if (!(json as any).success) {
      const err = new Error((json as any).error?.message || 'Request failed');
      (err as any).status = response.status;
      (err as any).code = (json as any).error?.code;
      throw err;
    }
    return (json as any).data as T;
  }
  if (!response.ok) {
    const err = new Error((json as any)?.message || 'Request failed');
    (err as any).status = response.status;
    throw err;
  }
  return json as T;
}

/**
 * Sign up new user
 */
export async function signup(data: SignupRequest): Promise<User> {
  const result = await apiRequest<User>('/signup', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return parseWithSchema(UserSchema, result);
}

/**
 * Log in user
 */
export async function login(data: LoginRequest): Promise<User> {
  const result = await apiRequest<User>('/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return parseWithSchema(UserSchema, result);
}

/**
 * Log out current user
 */
export async function logout(): Promise<void> {
  await apiRequest('/logout', {
    method: 'POST',
  });
}

/**
 * Get current user profile
 * 
 * Silently handles 401 (not authenticated) and network errors.
 * Returns null instead of throwing to prevent console noise.
 */
export async function me(): Promise<User | null> {
  try {
    const result = await apiRequest<User>('/me');
    return parseWithSchema(UserSchema, result);
  } catch (error: any) {
    // If not authenticated (401), return null instead of throwing
    // This is expected behavior when user is not logged in
    const status = error?.status;
    const msg = error?.message?.toLowerCase() || '';
    const isNetworkError = error?.isNetworkError || status === 0;
    
    // Silently handle 401 - this is expected when not logged in
    // Note: Browser will still show network error in console, but our code won't log it
    if (status === 401 || msg.includes('unauthorized') || msg.includes('not authenticated')) {
      // Return null silently - don't log or throw
      return null;
    }
    
    // Silently handle network errors - server might be down or network unstable
    if (isNetworkError || msg.includes('network error') || msg.includes('failed to fetch')) {
      // Return null silently for network errors during bootstrap
      // This prevents console spam when server is unavailable
      return null;
    }
    
    // Only throw for unexpected errors (not 401, not network errors)
    throw error;
  }
}

export interface UpdateProfileRequest {
  name?: string | null;
}

/**
 * Update user profile (name)
 */
export async function updateProfile(data: UpdateProfileRequest): Promise<User> {
  const result = await apiRequest<User>('/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  return parseWithSchema(UserSchema, result);
}

/**
 * Change user password
 */
export async function changePassword(data: ChangePasswordRequest): Promise<void> {
  await apiRequest('/change-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Request password reset token
 */
export async function forgotPassword(data: ForgotPasswordRequest): Promise<void> {
  await apiRequest('/forgot-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Reset password with token
 */
export async function resetPassword(data: ResetPasswordRequest): Promise<void> {
  await apiRequest('/reset-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Log out all devices
 */
export async function logoutAll(): Promise<void> {
  await apiRequest('/logout-all', {
    method: 'POST',
  });
}

/**
 * Get active sessions for current user
 */
export async function getSessions(): Promise<Session[]> {
  const result = await apiRequest<Session[]>('/sessions');
  return parseWithSchema(z.array(SessionSchema), result);
}

/**
 * Revoke a specific session
 */
export async function revokeSession(sessionId: number): Promise<void> {
  await apiRequest(`/sessions/${sessionId}`, {
    method: 'DELETE',
  });
}

export async function getAccount(): Promise<z.infer<typeof AccountSchema>> {
  const result = await accountRequest('/me');
  return parseWithSchema(AccountSchema, result);
}

export async function updateAccount(data: Partial<SignupRequest> & { timezone?: string; currency?: string; units?: string; theme?: string; personalization_opt_in?: boolean; preferences_json?: Record<string, unknown> | null; }): Promise<z.infer<typeof AccountSchema>> {
  const result = await accountRequest('/me', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  return parseWithSchema(AccountSchema, result);
}

export async function getPreferences() {
  const result = await accountRequest('/preferences');
  return parseWithSchema(PreferenceSchema, result);
}

export async function listConnectedAccounts() {
  return accountRequest('/oauth');
}

export async function googleStart(redirectUri?: string): Promise<{ redirect_url: string }> {
  const params = redirectUri ? `?redirect_uri_override=${encodeURIComponent(redirectUri)}` : '';
  return apiRequest(`/google/start${params}`);
}

export async function googleCallback(code: string, state: string): Promise<User> {
  const qs = new URLSearchParams({ code, state }).toString();
  const result = await apiRequest<User>(`/google/callback?${qs}`);
  return parseWithSchema(UserSchema, result);
}

export async function googleDisconnect(): Promise<void> {
  await apiRequest('/google/disconnect', { method: 'POST' });
}
