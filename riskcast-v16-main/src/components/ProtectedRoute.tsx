/**
 * Protected Route Component
 * 
 * RISKCAST Auth System - Phase 2
 * Protects routes that require authentication.
 */

import { useEffect, ReactNode } from 'react';
import { useAuth } from '../store/authStore';
import { shouldProtectRoute } from '../config/auth';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
  requireAuth?: boolean; // Override: force protection even if config says no
}

export function ProtectedRoute({ children, fallback, requireAuth = true }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const currentPath = window.location.pathname;
  const needsProtection = requireAuth && shouldProtectRoute(currentPath);

  // If route doesn't need protection, render children immediately (guest mode)
  if (!needsProtection) {
    return <>{children}</>;
  }

  useEffect(() => {
    // If route needs protection and user is not authenticated, redirect to login
    if (needsProtection && !isLoading && !isAuthenticated) {
      const search = window.location.search;
      // Preserve current path in query parameter for redirect after login
      window.location.href = `/?next=${encodeURIComponent(currentPath + search)}`;
    }
  }, [isAuthenticated, isLoading, needsProtection, currentPath]);

  // Show loading state while checking auth (only for protected routes)
  if (isLoading) {
    return (
      fallback || (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white/60">Checking authentication...</p>
          </div>
        </div>
      )
    );
  }

  // If not authenticated, show nothing (redirect will happen)
  if (!isAuthenticated) {
    return null;
  }

  // Render children if authenticated
  return <>{children}</>;
}
