import React, { useEffect, useState } from 'react';
import {
  Settings as SettingsIcon,
  Shield,
  KeyRound,
  Bot,
  Activity,
  CheckCircle2,
  AlertCircle,
  Building,
  User,
  Users,
  Bell,
  RefreshCw,
  Clock,
  Calendar,
  Lock,
  History,
  SlidersHorizontal
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useSearchParams } from 'react-router-dom';

export const Settings: React.FC = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'general';

  const [activeTab, setActiveTab] = useState<string>(initialTab);

  // Password state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<{ text: string; error: boolean } | null>(null);
  const [changingPass, setChangingPass] = useState(false);

  // Admin Diagnostics state
  const [diagnosticsData, setDiagnosticsData] = useState<any>(null);
  const [loadingDiag, setLoadingDiag] = useState(false);

  // User Management state (for Admin)
  const [usersList, setUsersList] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  // Notification Preferences state
  const [preferences, setPreferences] = useState<any>(null);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefSaved, setPrefSaved] = useState(false);

  useEffect(() => {
    const tabParam = searchParams.get('tab');
    if (tabParam) {
      setActiveTab(tabParam);
    }
  }, [searchParams]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  const fetchAdminDiagnostics = async () => {
    if (user?.role !== 'admin') return;
    setLoadingDiag(true);
    try {
      const res = await api.get('/system/diagnostics');
      setDiagnosticsData(res.data);
    } catch (e: any) {
      setDiagnosticsData(null);
    } finally {
      setLoadingDiag(false);
    }
  };

  const fetchUsers = async () => {
    if (user?.role !== 'admin') return;
    setLoadingUsers(true);
    try {
      const res = await api.get('/employees?limit=20');
      setUsersList(res.data || []);
    } catch (e) {
      console.error('Failed to load users:', e);
    } finally {
      setLoadingUsers(false);
    }
  };

  const fetchPreferences = async () => {
    try {
      const res = await api.get('/notifications/preferences');
      setPreferences(res.data);
    } catch (e) {
      console.error('Failed to load notification preferences:', e);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin' && activeTab === 'diagnostics') {
      fetchAdminDiagnostics();
    }
    if (user?.role === 'admin' && activeTab === 'users') {
      fetchUsers();
    }
    if (activeTab === 'notifications') {
      fetchPreferences();
    }
  }, [activeTab, user]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg(null);
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ text: 'New passwords do not match.', error: true });
      return;
    }
    if (newPassword.length < 8) {
      setPasswordMsg({ text: 'Password must be at least 8 characters long.', error: true });
      return;
    }

    setChangingPass(true);
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMsg({ text: 'Password updated successfully.', error: false });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPasswordMsg({
        text: err.response?.data?.detail || 'Failed to update password.',
        error: true,
      });
    } finally {
      setChangingPass(false);
    }
  };

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingPrefs(true);
    try {
      const res = await api.put('/notifications/preferences', preferences);
      setPreferences(res.data);
      setPrefSaved(true);
      setTimeout(() => setPrefSaved(false), 2000);
    } catch (e) {
      console.error('Failed to save preferences:', e);
    } finally {
      setSavingPrefs(false);
    }
  };

  const role = user?.role || 'employee';

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="pb-4 border-b border-border">
        <h1 className="text-xl font-bold text-dark tracking-tight">
          {role === 'admin' ? 'System Settings & Diagnostics' : 'Account & Personal Settings'}
        </h1>
        <p className="text-xs text-secondary mt-0.5">
          {role === 'admin'
            ? 'Manage organization parameters, attendance rules, user roles, and system operations.'
            : 'Manage your profile details, password security, and notification preferences.'}
        </p>
      </div>

      {/* Role-Specific Navigation Tabs */}
      <div className="flex items-center gap-1 border-b border-border text-xs">
        {role === 'admin' && (
          <>
            <button
              onClick={() => handleTabChange('general')}
              className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
                activeTab === 'general'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-secondary hover:text-dark'
              }`}
            >
              Organization & Rules
            </button>
            <button
              onClick={() => handleTabChange('users')}
              className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
                activeTab === 'users'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-secondary hover:text-dark'
              }`}
            >
              User Management
            </button>
            <button
              onClick={() => handleTabChange('diagnostics')}
              className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
                activeTab === 'diagnostics'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-secondary hover:text-dark'
              }`}
            >
              System Diagnostics
            </button>
          </>
        )}

        {(role === 'hr_manager' || role === 'employee') && (
          <button
            onClick={() => handleTabChange('profile')}
            className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
              activeTab === 'profile' || activeTab === 'general'
                ? 'border-primary text-primary'
                : 'border-transparent text-secondary hover:text-dark'
            }`}
          >
            My Profile
          </button>
        )}

        <button
          onClick={() => handleTabChange('security')}
          className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
            activeTab === 'security'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-dark'
          }`}
        >
          Security & Password
        </button>

        <button
          onClick={() => handleTabChange('notifications')}
          className={`px-4 py-2 font-semibold border-b-2 transition-colors ${
            activeTab === 'notifications'
              ? 'border-primary text-primary'
              : 'border-transparent text-secondary hover:text-dark'
          }`}
        >
          Notifications
        </button>
      </div>

      {/* TAB 1: General / Organization Settings (Admin) */}
      {role === 'admin' && activeTab === 'general' && (
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
            <div className="flex items-center gap-2">
              <Building className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-bold text-dark">Organization Profile</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block">Organization Name</span>
                <span className="font-semibold text-dark text-sm block mt-0.5">
                  {user?.organization_name || 'AttendAI Global'}
                </span>
              </div>
              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block">System Timezone</span>
                <span className="font-semibold text-dark text-sm block mt-0.5">UTC (Localized Display)</span>
              </div>
              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block">Workweek Policy</span>
                <span className="font-semibold text-dark text-sm block mt-0.5">Monday – Friday (40h)</span>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-bold text-dark">Workforce Attendance & Overtime Rules</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-50 border border-border rounded-lg space-y-1">
                <span className="text-secondary block font-semibold">Standard Shift Grace Period</span>
                <span className="text-dark font-bold text-sm block">15 Minutes</span>
                <p className="text-[11px] text-secondary">
                  Arrivals within 15 minutes of scheduled shift start are marked on-time.
                </p>
              </div>
              <div className="p-3 bg-slate-50 border border-border rounded-lg space-y-1">
                <span className="text-secondary block font-semibold">Overtime Calculation Threshold</span>
                <span className="text-dark font-bold text-sm block">Daily Shift Required Hours (8.0h)</span>
                <p className="text-[11px] text-secondary">
                  Overtime is automatically calculated beyond required shift hours.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB: My Profile (HR / Employee) */}
      {(role === 'hr_manager' || role === 'employee') && (activeTab === 'profile' || activeTab === 'general') && (
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-bold text-dark">Employee Information</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3 bg-slate-50 border border-border rounded-lg">
              <span className="text-secondary block">Full Name</span>
              <span className="font-semibold text-dark text-sm block mt-0.5">
                {user?.first_name} {user?.last_name}
              </span>
            </div>
            <div className="p-3 bg-slate-50 border border-border rounded-lg">
              <span className="text-secondary block">Employee Code</span>
              <span className="font-mono font-bold text-primary text-sm block mt-0.5">
                {user?.employee_code || 'EMP001'}
              </span>
            </div>
            <div className="p-3 bg-slate-50 border border-border rounded-lg">
              <span className="text-secondary block">Account Role</span>
              <span className="font-semibold text-dark text-sm block mt-0.5 capitalize">
                {role.replace('_', ' ')}
              </span>
            </div>
            <div className="p-3 bg-slate-50 border border-border rounded-lg">
              <span className="text-secondary block">Email Address</span>
              <span className="font-semibold text-dark text-sm block mt-0.5 truncate">{user?.email}</span>
            </div>
            <div className="p-3 bg-slate-50 border border-border rounded-lg">
              <span className="text-secondary block">Organization</span>
              <span className="font-semibold text-dark text-sm block mt-0.5">
                {user?.organization_name || 'AttendAI Global'}
              </span>
            </div>
            <div className="p-3 bg-slate-50 border border-border rounded-lg">
              <span className="text-secondary block">Status</span>
              <span className="font-semibold text-emerald-600 text-sm block mt-0.5">Active</span>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: User Management (Admin Only) */}
      {role === 'admin' && activeTab === 'users' && (
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div>
              <h2 className="text-xs font-bold text-dark">User & Staff Directory</h2>
              <p className="text-[11px] text-secondary mt-0.5">Active workforce accounts and system roles</p>
            </div>
            <button
              onClick={fetchUsers}
              disabled={loadingUsers}
              className="px-3 py-1 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-50 flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingUsers ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-secondary text-[11px]">
                  <th className="pb-2 font-semibold">Employee</th>
                  <th className="pb-2 font-semibold">Code</th>
                  <th className="pb-2 font-semibold">Email</th>
                  <th className="pb-2 font-semibold">Designation</th>
                  <th className="pb-2 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {usersList.map((emp) => (
                  <tr key={emp.id} className="hover:bg-slate-50/50">
                    <td className="py-2.5 font-medium text-dark">
                      {emp.first_name} {emp.last_name}
                    </td>
                    <td className="py-2.5 font-mono text-primary font-semibold">{emp.employee_code}</td>
                    <td className="py-2.5 text-secondary">{emp.email}</td>
                    <td className="py-2.5 text-secondary">{emp.designation || 'Staff'}</td>
                    <td className="py-2.5">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Active
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Admin Diagnostics (Admin Only) */}
      {role === 'admin' && activeTab === 'diagnostics' && (
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary" />
                <h2 className="text-xs font-bold text-dark">System & Infrastructure Diagnostics</h2>
              </div>
              <button
                onClick={fetchAdminDiagnostics}
                disabled={loadingDiag}
                className="px-3 py-1 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-50 flex items-center gap-1.5"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingDiag ? 'animate-spin' : ''}`} />
                <span>Refresh Diagnostics</span>
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block font-semibold">Primary LLM Provider</span>
                <span className="font-mono text-primary font-bold text-sm block mt-1 uppercase">
                  {diagnosticsData?.llm_diagnostics?.active_provider || 'NVIDIA NIM'}
                </span>
                <span className="text-[10px] text-secondary block mt-0.5">
                  Model: {diagnosticsData?.llm_diagnostics?.nvidia_nim?.model || 'Mistral Large 4'}
                </span>
              </div>

              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block font-semibold">Fallback LLM Provider</span>
                <span className="font-mono text-purple-700 font-bold text-sm block mt-1">
                  GroqCloud (GPT-OSS-120B)
                </span>
                <span className="text-[10px] text-success block mt-0.5">Automatic failover configured</span>
              </div>

              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block font-semibold">Database Engine</span>
                <span className="font-semibold text-dark text-sm block mt-1">
                  {diagnosticsData?.database_diagnostics?.dialect || 'PostgreSQL (Asyncpg)'}
                </span>
                <span className="text-[10px] text-success block mt-0.5">Connection pool healthy</span>
              </div>

              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block font-semibold">Cache & Work Queue</span>
                <span className="font-semibold text-dark text-sm block mt-1">
                  {diagnosticsData?.redis_diagnostics?.mode || 'Distributed Cache'}
                </span>
                <span className="text-[10px] text-success block mt-0.5">Operational</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-border rounded-lg text-xs flex items-center justify-between">
              <div>
                <span className="font-bold text-dark block">Background Workers & Schedulers</span>
                <span className="text-[11px] text-secondary">
                  Attendance anomaly detection & policy indexing jobs active.
                </span>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                Healthy
              </span>
            </div>
          </div>
        </div>
      )}

      {/* TAB: Security & Password Management (All Roles) */}
      {activeTab === 'security' && (
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4 max-w-lg">
          <div className="flex items-center gap-2">
            <KeyRound className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-bold text-dark">Password Management</h2>
          </div>

          {passwordMsg && (
            <div
              className={`p-3 rounded-lg text-xs flex items-center gap-2 border ${
                passwordMsg.error ? 'bg-red-50 text-danger border-red-200' : 'bg-emerald-50 text-success border-emerald-200'
              }`}
            >
              {passwordMsg.error ? <AlertCircle className="w-4 h-4 flex-shrink-0" /> : <CheckCircle2 className="w-4 h-4 flex-shrink-0" />}
              <span>{passwordMsg.text}</span>
            </div>
          )}

          <form onSubmit={handlePasswordChange} className="space-y-3 text-xs">
            <div>
              <label className="block font-medium text-dark mb-1">Current Password</label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full px-3 py-1.5 bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
              />
            </div>

            <div>
              <label className="block font-medium text-dark mb-1">New Password (minimum 8 characters)</label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full px-3 py-1.5 bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
              />
            </div>

            <div>
              <label className="block font-medium text-dark mb-1">Confirm New Password</label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-1.5 bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
              />
            </div>

            <button
              type="submit"
              disabled={changingPass}
              className="px-4 py-2 bg-primary text-white font-semibold rounded-lg hover:bg-primary-hover shadow-sm disabled:opacity-50"
            >
              {changingPass ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>
      )}

      {/* TAB: Notifications Preferences (All Roles) */}
      {activeTab === 'notifications' && preferences && (
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4 max-w-lg text-xs">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <Bell className="w-4 h-4 text-primary" />
            <h2 className="text-sm font-bold text-dark">Notification Preferences</h2>
          </div>

          {prefSaved && (
            <div className="p-3 rounded-lg bg-emerald-50 text-success border border-emerald-200 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Preferences saved successfully!</span>
            </div>
          )}

          <form onSubmit={handleSavePreferences} className="space-y-4">
            <div className="space-y-2">
              <span className="font-bold text-dark block">Delivery Channels</span>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.in_app_enabled}
                  onChange={(e) =>
                    setPreferences({ ...preferences, in_app_enabled: e.target.checked })
                  }
                  className="rounded text-primary focus:ring-primary"
                />
                <span>In-App Notifications (Navbar Bell & Toasts)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={preferences.email_enabled}
                  onChange={(e) =>
                    setPreferences({ ...preferences, email_enabled: e.target.checked })
                  }
                  className="rounded text-primary focus:ring-primary"
                />
                <span>Email Notifications for Critical Alerts</span>
              </label>
            </div>

            <div className="space-y-2 pt-2 border-t border-border">
              <span className="font-bold text-dark block">Subscribed Event Categories</span>
              {Object.keys(preferences.categories || {}).map((cat) => (
                <label key={cat} className="flex items-center gap-2 cursor-pointer capitalize">
                  <input
                    type="checkbox"
                    checked={preferences.categories[cat]}
                    onChange={(e) =>
                      setPreferences({
                        ...preferences,
                        categories: {
                          ...preferences.categories,
                          [cat]: e.target.checked
                        }
                      })
                    }
                    className="rounded text-primary focus:ring-primary"
                  />
                  <span>{cat.replace('_', ' ')} Notifications</span>
                </label>
              ))}
            </div>

            <button
              type="submit"
              disabled={savingPrefs}
              className="px-4 py-2 bg-primary text-white font-semibold rounded-lg hover:bg-primary-hover shadow-sm disabled:opacity-50"
            >
              {savingPrefs ? 'Saving...' : 'Save Notification Preferences'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
