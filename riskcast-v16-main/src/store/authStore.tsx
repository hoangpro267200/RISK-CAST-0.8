/**
 * Authentication Store
 * 
 * RISKCAST Auth System - Phase 2
 * React Context-based auth state management (similar to useAiDockState pattern).
 */

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import * as authApi from '../api/auth';
import { shouldProtectRoute } from '../config/auth';
import type { User, LoginRequest, SignupRequest, ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest } from '../api/auth';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  signup: (email: string, password: string, name?: string) => Promise<void>;
  bootstrap: () => Promise<void>;
  changePassword: (current: string, newPassword: string) => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// Create context with default value
const defaultAuthValue: AuthContextValue = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  login: async () => {},
  logout: async () => {},
  signup: async () => {},
  bootstrap: async () => {},
  changePassword: async () => {},
  forgotPassword: async () => {},
  resetPassword: async () => {},
  logoutAll: async () => {},
  refreshUser: async () => {},
};

const AuthContext = createContext<AuthContextValue>(defaultAuthValue);

/**
 * AuthProvider component - wrap app with this
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  /**
   * Bootstrap - check if user is authenticated on app init
   * 
   * Silently handles network errors and 401 responses:
   * - Network errors (ERR_NETWORK_CHANGED, Failed to fetch) are expected when server is unavailable
   * - 401 responses are expected when user is not logged in
   * - Only unexpected errors are logged to console
   */
  const bootstrap = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      // me() returns null for 401 and network errors, so no error is thrown
      // This prevents console spam during bootstrap when server is unavailable
      const user = await authApi.me();
      setState({
        user,
        isLoading: false,
        isAuthenticated: user !== null,
      });
    } catch (error: any) {
      // This catch block should rarely execute since me() handles 401 and network errors silently
      // Only log truly unexpected errors
      const isAuthError = error instanceof Error && (
        error.message.toLowerCase().includes('unauthorized') ||
        error.message.toLowerCase().includes('401') ||
        error.message.toLowerCase().includes('not authenticated')
      );
      
      const isNetworkError = 
        error?.isNetworkError ||
        error?.status === 0 ||
        (error instanceof Error && (
          error.message.toLowerCase().includes('network error') ||
          error.message.toLowerCase().includes('failed to fetch') ||
          error.message.toLowerCase().includes('err_network_changed')
        ));
      
      // Don't log network errors or auth errors - these are expected and handled gracefully
      // Network errors are common during development when server restarts or network is unstable
      // 401 errors are expected when user is not authenticated
      if (!isAuthError && !isNetworkError) {
        // Only log unexpected errors (e.g., 500 server errors, parsing errors, etc.)
        console.error('[AuthStore] Bootstrap error:', error);
      } else if (import.meta.env.MODE === 'development') {
        // Optional: Log silently in dev mode for debugging (can be removed in production)
        // Uncomment the line below if you need to debug network/auth issues:
        // console.debug('[AuthStore] Bootstrap: Network/auth error handled silently', { isAuthError, isNetworkError });
      }
      
      // Always set state to unauthenticated on any error
      // This ensures the app continues to work even when auth check fails
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
    }
  }, []);

  /**
   * Login user
   */
  const login = useCallback(async (email: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      const user = await authApi.login({ email, password });
      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
      });
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, []);

  /**
   * Logout user
   */
  const logout = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      await authApi.logout();
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
    } catch (error) {
      // Even if logout fails, clear local state
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
      throw error;
    }
  }, []);

  /**
   * Sign up new user
   */
  const signup = useCallback(async (email: string, password: string, name?: string) => {
    setState(prev => ({ ...prev, isLoading: true }));
    try {
      const user = await authApi.signup({ email, password, name });
      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
      });
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, []);

  /**
   * Change password
   */
  const changePassword = useCallback(async (current: string, newPassword: string) => {
    await authApi.changePassword({ current_password: current, new_password: newPassword });
    // Refresh user after password change
    await refreshUser();
  }, []);

  /**
   * Forgot password
   */
  const forgotPassword = useCallback(async (email: string) => {
    await authApi.forgotPassword({ email });
  }, []);

  /**
   * Reset password
   */
  const resetPassword = useCallback(async (token: string, newPassword: string) => {
    await authApi.resetPassword({ token, new_password: newPassword });
  }, []);

  /**
   * Logout all devices
   */
  const logoutAll = useCallback(async () => {
    await authApi.logoutAll();
    setState({
      user: null,
      isLoading: false,
      isAuthenticated: false,
    });
  }, []);

  /**
   * Refresh current user data
   */
  const refreshUser = useCallback(async () => {
    try {
      const user = await authApi.me();
      setState(prev => ({
        ...prev,
        user,
        isAuthenticated: user !== null,
      }));
    } catch (error) {
      // If unauthorized, clear user
      setState(prev => ({
        ...prev,
        user: null,
        isAuthenticated: false,
      }));
    }
  }, []);

  // Bootstrap on mount - only if route might need auth
  // This prevents unnecessary 401 calls for guest-accessible routes
  useEffect(() => {
    const currentPath = window.location.pathname;
    
    // Guest routes that should NEVER trigger auth check
    // These routes work without authentication
    const guestRoutes = [
      '/input',
      '/input_react',
      '/results',
      '/summary',
      '/shipments',
      '/home',
      '/login',
      '/signup',
    ];
    
    const isGuestRoute = guestRoutes.some(route => 
      currentPath === route || currentPath.startsWith(route + '/')
    );
    
    if (isGuestRoute && !shouldProtectRoute(currentPath)) {
      // Guest route - set anonymous state immediately without API call
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
      return;
    }
    
    // Routes that definitely need auth check
    const requiresAuthCheck = 
      currentPath === '/overview' ||
      currentPath.startsWith('/overview/');
    
    if (requiresAuthCheck) {
      // Route definitely needs auth check
      bootstrap();
      return;
    }
    
    // For other routes, check config
    if (shouldProtectRoute(currentPath)) {
      bootstrap();
    } else {
      // Route doesn't need auth, set state to unauthenticated without API call
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
      });
    }
  }, [bootstrap]);

  const value: AuthContextValue = {
    ...state,
    login,
    logout,
    signup,
    bootstrap,
    changePassword,
    forgotPassword,
    resetPassword,
    logoutAll,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access auth state
 */
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
