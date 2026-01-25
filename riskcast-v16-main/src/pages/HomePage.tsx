/**
 * Home Page
 * 
 * RISKCAST Auth System - Phase 2
 * Shows login form when not authenticated, welcome screen when authenticated.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../store/authStore';
import * as authApi from '../api/auth';

export default function HomePage() {
  const { user, isAuthenticated, isLoading, logout, login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [inlineError, setInlineError] = useState<string | null>(null);
  const [authConfig, setAuthConfig] = useState<authApi.AuthConfig | null>(null);

  // Fetch auth config to know which auth methods are available
  useEffect(() => {
    authApi.getAuthConfig()
      .then(setAuthConfig)
      .catch(err => console.warn('Failed to fetch auth config:', err));
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      window.location.href = '/';
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white/60">Loading...</p>
        </div>
      </div>
    );
  }

  // Not authenticated - show login form
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">RISKCAST</h1>
              <p className="text-slate-400">Sign in to your account</p>
            </div>

            {/* Login form */}
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData(e.currentTarget);
                const email = (formData.get('email') as string)?.trim();
                const password = formData.get('password') as string;
                
                try {
                  await login(email, password);
                  // Redirect to home after successful login
                  window.location.href = '/';
                } catch (error) {
                  console.error('Login error:', error);
                  setInlineError(error instanceof Error ? error.message : 'Login failed. Please check your credentials.');
                }
              }}
              className="space-y-6"
            >
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  placeholder="••••••••"
                />
                <div className="mt-2 flex items-center justify-between">
                  <a
                    href="/forgot-password"
                    className="text-sm text-blue-400 hover:text-blue-300 transition"
                  >
                    Forgot password?
                  </a>
                  <button
                    type="button"
                    onClick={() => setShowPassword((p) => !p)}
                    className="text-sm text-slate-300 hover:text-white transition"
                  >
                    {showPassword ? 'Hide' : 'Show'} password
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition"
              >
                Sign In
              </button>

              {/* Only show Google button if Google OAuth is configured */}
              {authConfig?.google_enabled && (
                <button
                  type="button"
                  onClick={async () => {
                    setIsGoogleLoading(true);
                    setInlineError(null);
                    try {
                      const { redirect_url } = await authApi.googleStart(window.location.origin);
                      window.location.href = redirect_url;
                    } catch (err: any) {
                      setInlineError(err?.message || 'Failed to start Google login');
                      setIsGoogleLoading(false);
                    }
                  }}
                  disabled={isGoogleLoading}
                  className="w-full py-3 bg-white/90 hover:bg-white text-slate-900 font-medium rounded-lg transition flex items-center justify-center gap-2 border border-slate-200"
                >
                  {isGoogleLoading ? 'Redirecting…' : 'Continue with Google'}
                </button>
              )}
            </form>

            {inlineError && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 text-red-300 rounded-lg text-sm">
                {inlineError}
              </div>
            )}

            {/* Sign up link */}
            <div className="mt-6 text-center">
              <p className="text-slate-400 text-sm">
                Don't have an account?{' '}
                <a href="/signup" className="text-blue-400 hover:text-blue-300 transition">
                  Sign up
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Authenticated - show welcome screen
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          {/* Welcome header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">
              Welcome back, {user.name || user.email}!
            </h1>
            <p className="text-slate-400">What would you like to do today?</p>
          </div>

          {/* Action buttons */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <a
              href="/input_react"
              className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-blue-500 transition text-center group"
            >
              <div className="text-2xl mb-2">🆕</div>
              <h3 className="font-semibold text-white mb-1">New Analysis</h3>
              <p className="text-sm text-slate-400">Start a new risk analysis</p>
            </a>

            <a
              href="/results"
              className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-blue-500 transition text-center group"
            >
              <div className="text-2xl mb-2">📊</div>
              <h3 className="font-semibold text-white mb-1">View Results</h3>
              <p className="text-sm text-slate-400">View your latest analysis</p>
            </a>

            <a
              href="/overview"
              className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-blue-500 transition text-center group"
            >
              <div className="text-2xl mb-2">⚙️</div>
              <h3 className="font-semibold text-white mb-1">Account Overview</h3>
              <p className="text-sm text-slate-400">Manage your account</p>
            </a>

            <button
              onClick={handleLogout}
              className="p-6 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-red-500 transition text-center group"
            >
              <div className="text-2xl mb-2">🚪</div>
              <h3 className="font-semibold text-white mb-1">Sign Out</h3>
              <p className="text-sm text-slate-400">Log out of your account</p>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
