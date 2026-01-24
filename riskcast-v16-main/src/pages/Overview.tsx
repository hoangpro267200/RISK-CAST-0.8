/**
 * Account Overview Page
 * 
 * RISKCAST Auth System - Phase 3
 * Account management page with profile, security, sessions, and account deletion.
 */

import { useState, useEffect, FormEvent } from 'react';
import { useAuth } from '../store/authStore';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { GlassCard } from '../components/GlassCard';
import * as authApi from '../api/auth';
import type { Session } from '../api/auth';
import { updateProfile, getAccount, updateAccount, getPreferences, listConnectedAccounts, googleDisconnect } from '../api/auth';
import { 
  User, Lock, Smartphone, Trash2, ArrowLeft, Save, 
  CheckCircle2, XCircle, AlertTriangle, RefreshCw,
  Shield, Key, LogOut, Calendar, Monitor
} from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

export default function OverviewPage() {
  const { user, isLoading: authLoading, changePassword, logout, logoutAll, refreshUser } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  
  // Profile state
  const [name, setName] = useState('');
  const [nameEditing, setNameEditing] = useState(false);
  const [savingName, setSavingName] = useState(false);
  
  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  
  // Delete account state
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [preferences, setPreferences] = useState({
    timezone: '',
    currency: '',
    units: '',
    theme: '',
    personalization_opt_in: false,
  });
  const [connectedAccounts, setConnectedAccounts] = useState<{ provider: string; email?: string; connected_at?: string; disconnected_at?: string }[]>([]);
  const [savingPreferences, setSavingPreferences] = useState(false);

  // Initialize user data
  useEffect(() => {
    if (user) {
      setName(user.name || '');
    }
  }, [user]);

  // Load sessions
  useEffect(() => {
    loadSessions();
    loadAccountData();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await authApi.getSessions();
      setSessions(data);
    } catch (error) {
      showToast('error', 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const loadAccountData = async () => {
    try {
      const account = await getAccount();
      setName(account.name || '');
      setPreferences({
        timezone: account.preferences.timezone || '',
        currency: account.preferences.currency || '',
        units: account.preferences.units || '',
        theme: account.preferences.theme || '',
        personalization_opt_in: account.preferences.personalization_opt_in ?? false,
      });
      const connected = await listConnectedAccounts();
      const normalized = Array.isArray(connected) ? connected : [];
      setConnectedAccounts(normalized);
    } catch (error) {
      showToast('error', 'Failed to load account data');
    }
  };

  const showToast = (type: ToastType, message: string) => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  };

  const handleSaveName = async (e: FormEvent) => {
    e.preventDefault();
    setSavingName(true);
    try {
      await updateProfile({ name: name || null });
      await refreshUser();
      setNameEditing(false);
      showToast('success', 'Name updated successfully');
    } catch (error) {
      showToast('error', 'Failed to update name');
    } finally {
      setSavingName(false);
    }
  };

  const handleChangePassword = async (e: FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      showToast('error', 'New passwords do not match');
      return;
    }
    
    setChangingPassword(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowPasswordForm(false);
      showToast('success', 'Password changed successfully');
    } catch (error) {
      showToast('error', error instanceof Error ? error.message : 'Failed to change password');
    } finally {
      setChangingPassword(false);
    }
  };

  const handleRevokeSession = async (sessionId: number) => {
    try {
      await authApi.revokeSession(sessionId);
      await loadSessions();
      showToast('success', 'Session revoked');
    } catch (error) {
      showToast('error', 'Failed to revoke session');
    }
  };

  const handleLogoutAll = async () => {
    try {
      await logoutAll();
      showToast('success', 'Logged out from all devices');
      await loadSessions();
    } catch (error) {
      showToast('error', 'Failed to log out all devices');
    }
  };

  const handleSavePreferences = async () => {
    setSavingPreferences(true);
    try {
      await updateAccount({
        timezone: preferences.timezone,
        currency: preferences.currency,
        units: preferences.units,
        theme: preferences.theme,
        personalization_opt_in: preferences.personalization_opt_in,
      });
      showToast('success', 'Preferences updated');
      await loadAccountData();
    } catch (error) {
      showToast('error', 'Failed to update preferences');
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleTogglePersonalization = async (value: boolean) => {
    setPreferences((prev) => ({ ...prev, personalization_opt_in: value }));
    try {
      await updateAccount({ personalization_opt_in: value });
      showToast('success', value ? 'Personalization enabled' : 'Personalization disabled');
    } catch (error) {
      showToast('error', 'Failed to update personalization');
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      await googleDisconnect();
      await loadAccountData();
      showToast('success', 'Google disconnected');
    } catch (error) {
      showToast('error', 'Failed to disconnect Google');
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') {
      showToast('error', 'Please type DELETE to confirm');
      return;
    }

    setDeletingAccount(true);
    try {
      // TODO: Add API endpoint to delete account
      await logout();
      showToast('success', 'Account deleted successfully');
      window.location.href = '/';
    } catch (error) {
      showToast('error', 'Failed to delete account');
      setDeletingAccount(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getBrowserName = (userAgent: string | null) => {
    if (!userAgent) return 'Unknown';
    if (userAgent.includes('Chrome')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    return 'Unknown';
  };

  const getOSName = (userAgent: string | null) => {
    if (!userAgent) return 'Unknown';
    if (userAgent.includes('Windows')) return 'Windows';
    if (userAgent.includes('Mac')) return 'macOS';
    if (userAgent.includes('Linux')) return 'Linux';
    if (userAgent.includes('Android')) return 'Android';
    if (userAgent.includes('iOS')) return 'iOS';
    return 'Unknown';
  };

  const Toast = ({ toast }: { toast: Toast }) => {
    const icons = {
      success: CheckCircle2,
      error: XCircle,
      warning: AlertTriangle,
      info: RefreshCw,
    };
    
    const colors = {
      success: '#10b981',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6',
    };
    
    const Icon = icons[toast.type];
    const color = colors[toast.type];
    
    return (
      <div
        className="flex items-center gap-3 px-4 py-3 bg-slate-900/90 backdrop-blur-xl border rounded-lg shadow-lg"
        style={{
          borderColor: `${color}40`,
          minWidth: '300px',
          maxWidth: '400px',
        }}
      >
        <Icon size={20} style={{ color }} className="flex-shrink-0" />
        <span className="text-white text-sm flex-1">{toast.message}</span>
        <button
          onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))}
          className="text-slate-400 hover:text-white transition"
        >
          <XCircle size={16} />
        </button>
      </div>
    );
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4 md:p-8">
        {/* Toast Container */}
        {toasts.length > 0 && (
          <div className="fixed top-20 right-4 z-50 flex flex-col gap-2">
            {toasts.map(toast => (
              <Toast key={toast.id} toast={toast} />
            ))}
          </div>
        )}

        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <a
                href="/"
                className="p-2 hover:bg-white/5 rounded-lg transition"
                title="Back to home"
              >
                <ArrowLeft className="w-6 h-6 text-white" />
              </a>
              <div>
                <h1 className="text-3xl font-bold text-white">Account Overview</h1>
                <p className="text-slate-400 mt-1">Manage your account settings</p>
              </div>
            </div>
          </div>

          {authLoading || loading ? (
            <GlassCard className="text-center py-12">
              <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-white/60">Loading...</p>
            </GlassCard>
          ) : (
            <>
              {/* Profile Section */}
              <GlassCard>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white">Profile</h2>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      readOnly
                      className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none cursor-not-allowed opacity-60"
                    />
                    <p className="text-xs text-slate-400 mt-1">Email cannot be changed</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Name
                    </label>
                    {nameEditing ? (
                      <form onSubmit={handleSaveName} className="flex gap-2">
                        <input
                          type="text"
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                          className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Enter your name"
                          required
                        />
                        <button
                          type="submit"
                          disabled={savingName}
                          className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition flex items-center gap-2"
                        >
                          <Save className="w-4 h-4" />
                          {savingName ? 'Saving...' : 'Save'}
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setName(user?.name || '');
                            setNameEditing(false);
                          }}
                          className="px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition"
                        >
                          Cancel
                        </button>
                      </form>
                    ) : (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={name || 'Not set'}
                          readOnly
                          className="flex-1 px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400"
                        />
                        <button
                          onClick={() => setNameEditing(true)}
                          className="px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition"
                        >
                          Edit
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </GlassCard>

              {/* Security Section */}
              <GlassCard>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-green-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white">Security</h2>
                </div>

                <div className="space-y-6">
                  {/* Password Change */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="font-medium text-white flex items-center gap-2">
                          <Key className="w-4 h-4" />
                          Password
                        </h3>
                        <p className="text-sm text-slate-400 mt-1">Last changed: Never</p>
                      </div>
                      {!showPasswordForm && (
                        <button
                          onClick={() => setShowPasswordForm(true)}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition"
                        >
                          Change Password
                        </button>
                      )}
                    </div>

                    {showPasswordForm && (
                      <form onSubmit={handleChangePassword} className="space-y-4 pt-4 border-t border-slate-700">
                        <div>
                          <label className="block text-sm font-medium text-slate-300 mb-2">
                            Current Password
                          </label>
                          <input
                            type="password"
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            required
                            autoComplete="current-password"
                            className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter current password"
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-slate-300 mb-2">
                            New Password
                          </label>
                          <input
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            required
                            autoComplete="new-password"
                            className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter new password"
                          />
                          <p className="text-xs text-slate-400 mt-1">
                            Must be at least 8 characters with uppercase, lowercase, number, and special character
                          </p>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-slate-300 mb-2">
                            Confirm New Password
                          </label>
                          <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            autoComplete="new-password"
                            className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Confirm new password"
                          />
                        </div>

                        <div className="flex gap-2">
                          <button
                            type="submit"
                            disabled={changingPassword}
                            className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition"
                          >
                            {changingPassword ? 'Changing...' : 'Update Password'}
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setShowPasswordForm(false);
                              setCurrentPassword('');
                              setNewPassword('');
                              setConfirmPassword('');
                            }}
                            className="px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition"
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    )}
                  </div>
                </div>
              </GlassCard>

              {/* Active Sessions Section */}
              <GlassCard>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                      <Smartphone className="w-5 h-5 text-purple-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Active Sessions</h2>
                  </div>
                  <button
                    onClick={handleLogoutAll}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition flex items-center gap-2"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign Out All Devices
                  </button>
                </div>

                <div className="space-y-3">
                  {sessions.length === 0 ? (
                    <p className="text-slate-400 text-center py-4">No active sessions</p>
                  ) : (
                    sessions.map((session) => (
                      <div
                        key={session.id}
                        className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
                            <Monitor className="w-5 h-5 text-purple-400" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white">
                                {getBrowserName(session.user_agent)} on {getOSName(session.user_agent)}
                              </span>
                              {session.is_valid && (
                                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
                                  Current
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-4 mt-1 text-sm text-slate-400">
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {formatDate(session.created_at)}
                              </span>
                              {session.ip_address && (
                                <span>{session.ip_address}</span>
                              )}
                            </div>
                          </div>
                        </div>
                        {session.is_valid ? (
                          <button
                            onClick={() => handleRevokeSession(session.id)}
                            className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm font-medium rounded-lg transition"
                          >
                            Revoke
                          </button>
                        ) : (
                          <span className="px-3 py-1.5 bg-slate-700/50 text-slate-400 text-sm rounded-lg">
                            Revoked
                          </span>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </GlassCard>

              {/* Connected Accounts */}
              <GlassCard>
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center">
                      <Lock className="w-5 h-5 text-blue-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-white">Connected Accounts</h2>
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        const { redirect_url } = await authApi.googleStart(window.location.origin + '/overview');
                        window.location.href = redirect_url;
                      } catch (error) {
                        showToast('error', 'Failed to start Google connect');
                      }
                    }}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition"
                  >
                    Connect Google
                  </button>
                </div>
                <div className="space-y-3">
                  {connectedAccounts.length === 0 ? (
                    <p className="text-slate-400 text-sm">No connected accounts yet.</p>
                  ) : (
                    connectedAccounts.map((acct) => (
                      <div key={acct.provider} className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                        <div>
                          <p className="text-white font-medium capitalize">{acct.provider}</p>
                          <p className="text-sm text-slate-400">{acct.email || 'Email not provided'}</p>
                        </div>
                        {acct.disconnected_at ? (
                          <span className="text-xs text-slate-400">Disconnected</span>
                        ) : (
                          <button
                            onClick={handleDisconnectGoogle}
                            className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-sm font-medium rounded-lg transition"
                          >
                            Disconnect
                          </button>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </GlassCard>

              {/* Preferences & Personalization */}
              <GlassCard>
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-teal-500/20 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-teal-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white">Preferences</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Timezone</label>
                    <input
                      value={preferences.timezone}
                      onChange={(e) => setPreferences((p) => ({ ...p, timezone: e.target.value }))}
                      className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                      placeholder="e.g., UTC, America/Los_Angeles"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Currency</label>
                    <input
                      value={preferences.currency}
                      onChange={(e) => setPreferences((p) => ({ ...p, currency: e.target.value }))}
                      className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                      placeholder="USD, EUR..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Units</label>
                    <input
                      value={preferences.units}
                      onChange={(e) => setPreferences((p) => ({ ...p, units: e.target.value }))}
                      className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                      placeholder="metric / imperial"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Theme</label>
                    <input
                      value={preferences.theme}
                      onChange={(e) => setPreferences((p) => ({ ...p, theme: e.target.value }))}
                      className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                      placeholder="light / dark / system"
                    />
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <div className="flex items-center gap-3">
                    <input
                      id="personalization"
                      type="checkbox"
                      className="w-4 h-4"
                      checked={preferences.personalization_opt_in}
                      onChange={(e) => handleTogglePersonalization(e.target.checked)}
                    />
                    <label htmlFor="personalization" className="text-sm text-slate-200">
                      Personalization opt-in (use my data to improve recommendations)
                    </label>
                  </div>
                  <button
                    onClick={handleSavePreferences}
                    disabled={savingPreferences}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition disabled:bg-blue-800 disabled:cursor-not-allowed"
                  >
                    {savingPreferences ? 'Saving...' : 'Save Preferences'}
                  </button>
                </div>
                <p className="mt-3 text-xs text-slate-400">
                  Data usage: we use account preferences and opt-in signals to tailor insights. You can export or request deletion from the data controls below.
                </p>
              </GlassCard>

              {/* Danger Zone */}
              <GlassCard className="border-red-500/20">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                    <AlertTriangle className="w-5 h-5 text-red-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white">Danger Zone</h2>
                </div>

                <div className="space-y-4">
                  {!showDeleteConfirm ? (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                      <h3 className="font-medium text-white mb-2">Delete Account</h3>
                      <p className="text-sm text-slate-400 mb-4">
                        Once you delete your account, there is no going back. Please be certain.
                      </p>
                      <button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition flex items-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        Delete Account
                      </button>
                    </div>
                  ) : (
                    <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg space-y-4">
                      <div>
                        <h3 className="font-medium text-white mb-2">Confirm Account Deletion</h3>
                        <p className="text-sm text-slate-400 mb-4">
                          This action cannot be undone. This will permanently delete your account and all associated data.
                        </p>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                          Type <span className="font-mono text-red-400">DELETE</span> to confirm:
                        </label>
                        <input
                          type="text"
                          value={deleteConfirmText}
                          onChange={(e) => setDeleteConfirmText(e.target.value)}
                          className="w-full px-4 py-3 bg-slate-800/50 border border-red-500/50 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          placeholder="Type DELETE to confirm"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleDeleteAccount}
                          disabled={deletingAccount || deleteConfirmText !== 'DELETE'}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 disabled:cursor-not-allowed text-white font-medium rounded-lg transition flex items-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          {deletingAccount ? 'Deleting...' : 'Yes, Delete My Account'}
                        </button>
                        <button
                          onClick={() => {
                            setShowDeleteConfirm(false);
                            setDeleteConfirmText('');
                          }}
                          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </GlassCard>
            </>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
}
