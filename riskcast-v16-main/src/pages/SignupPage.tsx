/**
 * Signup Page
 * 
 * RISKCAST Auth System - Phase 2
 * User registration page with email, password, and name.
 */

import { useState, FormEvent } from 'react';
import { useAuth } from '../store/authStore';
import * as authApi from '../api/auth';

export default function SignupPage() {
  const { signup, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);

    try {
      await signup(email, password, name || undefined);
      setSuccess(true);
      
      // Redirect to home after successful signup
      setTimeout(() => {
        window.location.href = '/';
      }, 1500);
    } catch (err: any) {
      // Extract error message properly
      let errorMessage = 'Signup failed. Please try again.';
      
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.message) {
        errorMessage = err.message;
      } else if (err?.detail) {
        // Handle FastAPI error format
        if (Array.isArray(err.detail)) {
          errorMessage = err.detail
            .map((e: any) => {
              const field = Array.isArray(e.loc) ? e.loc.slice(1).join('.') : 'field';
              return `${field}: ${e.msg || e.message || 'Invalid value'}`;
            })
            .join(', ');
        } else {
          errorMessage = err.detail;
        }
      } else if (err?.error?.message) {
        errorMessage = err.error.message;
      }
      
      setError(errorMessage);
    }
  };

  const handleGoogle = async () => {
    setIsGoogleLoading(true);
    setError(null);
    try {
      const { redirect_url } = await authApi.googleStart(window.location.origin + '/signup');
      window.location.href = redirect_url;
    } catch (err: any) {
      setError(err?.message || 'Failed to start Google signup');
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Create Account</h1>
            <p className="text-slate-400">Sign up for RISKCAST</p>
          </div>

          {/* Success message */}
          {success && (
            <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm">
              Account created successfully! Redirecting...
            </div>
          )}

          {/* Error message */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Signup form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-2">
                Name (optional)
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                placeholder="John Doe"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-2">
                Email *
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                placeholder="you@example.com"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password *
              </label>
              <div className="flex items-center gap-2">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  placeholder="••••••••"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((p) => !p)}
                  className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-xs text-white rounded-lg transition"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <p className="mt-2 text-xs text-slate-400">
                Must be at least 8 characters with uppercase, lowercase, number, and special character
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition"
            >
              {isLoading ? 'Creating account...' : 'Sign Up'}
            </button>

            <button
              type="button"
              onClick={handleGoogle}
              disabled={isLoading || isGoogleLoading}
              className="w-full py-3 bg-white/90 hover:bg-white text-slate-900 font-medium rounded-lg transition flex items-center justify-center gap-2 border border-slate-200"
            >
              {isGoogleLoading ? 'Redirecting…' : 'Continue with Google'}
            </button>
          </form>

          {/* Login link */}
          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">
              Already have an account?{' '}
              <a href="/login" className="text-blue-400 hover:text-blue-300 transition">
                Sign in
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
