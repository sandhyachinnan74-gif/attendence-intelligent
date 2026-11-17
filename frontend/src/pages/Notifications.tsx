import React, { useEffect, useState } from 'react';
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
  Search,
  Filter,
  CheckCheck,
  Archive,
  ArrowRight,
  RefreshCw,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  SlidersHorizontal,
  X
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export const NotificationsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [unreadOnly, setUnreadOnly] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  // Preferences Modal
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<any>(null);
  const [prefSaving, setPrefSaving] = useState(false);
  const [prefSuccess, setPrefSuccess] = useState(false);

  const categories = [
    { id: 'all', label: 'All Categories' },
    { id: 'attendance', label: 'Attendance' },
    { id: 'leave', label: 'Leave' },
    { id: 'shifts', label: 'Shifts' },
    { id: 'anomalies', label: 'Anomalies' },
    { id: 'approvals', label: 'Approvals' },
    { id: 'policies', label: 'Policies' },
    ...(user?.role === 'admin' ? [{ id: 'system', label: 'System' }] : [])
  ];

  const priorities = [
    { id: 'all', label: 'All Priorities' },
    { id: 'critical', label: 'Critical' },
    { id: 'warning', label: 'Warning' },
    { id: 'success', label: 'Success' },
    { id: 'information', label: 'Information' }
  ];

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        unread_only: unreadOnly ? 'true' : 'false'
      });
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      if (selectedPriority !== 'all') params.append('priority', selectedPriority);
      if (searchQuery.trim()) params.append('search', searchQuery.trim());

      const res = await api.get(`/notifications?${params.toString()}`);
      setNotifications(res.data.items || []);
      setTotal(res.data.total || 0);
      setUnreadCount(res.data.unread_count || 0);
    } catch (e) {
      console.error('Failed to load notifications:', e);
    } finally {
      setLoading(false);
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
    fetchNotifications();
  }, [selectedCategory, selectedPriority, unreadOnly, page]);

  useEffect(() => {
    fetchPreferences();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchNotifications();
  };

  const handleMarkAsRead = async (id: string, link?: string) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
      if (link) {
        navigate(link);
      }
    } catch (e) {
      console.error('Failed to mark read:', e);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (e) {
      console.error('Failed to mark all read:', e);
    }
  };

  const handleArchive = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.patch(`/notifications/${id}/archive`);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      setTotal((t) => Math.max(0, t - 1));
    } catch (err) {
      console.error('Failed to archive notification:', err);
    }
  };

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setPrefSaving(true);
    try {
      const res = await api.put('/notifications/preferences', preferences);
      setPreferences(res.data);
      setPrefSuccess(true);
      setTimeout(() => {
        setPrefSuccess(false);
        setShowPreferences(false);
      }, 1000);
    } catch (err) {
      console.error('Failed to save preferences:', err);
    } finally {
      setPrefSaving(false);
    }
  };

  const getPriorityStyle = (priority: string) => {
    switch (priority) {
      case 'critical':
        return {
          bg: 'bg-red-50/70 border-red-200 text-danger',
          badge: 'bg-red-100 text-danger border-red-200',
          icon: <AlertCircle className="w-4 h-4 text-danger flex-shrink-0" />
        };
      case 'warning':
        return {
          bg: 'bg-amber-50/70 border-amber-200 text-warning',
          badge: 'bg-amber-100 text-amber-800 border-amber-200',
          icon: <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0" />
        };
      case 'success':
        return {
          bg: 'bg-emerald-50/70 border-emerald-200 text-success',
          badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
          icon: <CheckCircle2 className="w-4 h-4 text-success flex-shrink-0" />
        };
      default:
        return {
          bg: 'bg-blue-50/70 border-blue-200 text-primary',
          badge: 'bg-blue-100 text-primary border-blue-200',
          icon: <Info className="w-4 h-4 text-primary flex-shrink-0" />
        };
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-dark tracking-tight">Notification Center</h1>
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-primary text-white text-[11px] font-bold">
                {unreadCount} unread
              </span>
            )}
          </div>
          <p className="text-xs text-secondary mt-0.5">
            Operational alerts, attendance events, approval statuses, and policy notifications.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowPreferences(true)}
            className="px-3 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-50 flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-secondary" />
            <span>Preferences</span>
          </button>

          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              <span>Mark All as Read</span>
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-card border border-border rounded-xl p-4 shadow-card space-y-3">
        <div className="flex flex-col md:flex-row items-center justify-between gap-3">
          {/* Search Input */}
          <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search notifications..."
              className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </form>

          {/* Quick Filter Toggles */}
          <div className="flex items-center gap-2 w-full md:w-auto justify-end">
            <button
              onClick={() => {
                setUnreadOnly(!unreadOnly);
                setPage(1);
              }}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                unreadOnly
                  ? 'bg-primary text-white border-primary shadow-xs'
                  : 'bg-white text-secondary border-border hover:text-dark hover:bg-slate-50'
              }`}
            >
              Unread Only
            </button>

            <select
              value={selectedPriority}
              onChange={(e) => {
                setSelectedPriority(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 text-xs font-medium bg-white border border-border rounded-lg text-dark focus:outline-none"
            >
              {priorities.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>

            <button
              onClick={fetchNotifications}
              disabled={loading}
              className="p-1.5 rounded-lg border border-border text-secondary hover:text-dark hover:bg-slate-50"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pt-2 border-t border-border">
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => {
                setSelectedCategory(c.id);
                setPage(1);
              }}
              className={`px-3 py-1 rounded-full text-[11px] font-semibold whitespace-nowrap transition-colors ${
                selectedCategory === c.id
                  ? 'bg-dark text-white'
                  : 'bg-slate-100 text-secondary hover:text-dark hover:bg-slate-200'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Notifications List */}
      <div className="bg-card border border-border rounded-xl shadow-card divide-y divide-border overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-secondary text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-primary mb-2" />
            <span>Loading notifications...</span>
          </div>
        ) : notifications.length === 0 ? (
          <div className="p-12 text-center text-secondary text-xs space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
            <p className="font-semibold text-dark text-sm">No notifications found</p>
            <p className="text-secondary">Try adjusting your filters or search keywords.</p>
          </div>
        ) : (
          notifications.map((n) => {
            const style = getPriorityStyle(n.priority);
            return (
              <div
                key={n.id}
                onClick={() => handleMarkAsRead(n.id, n.link)}
                className={`p-4 hover:bg-slate-50/80 transition-colors flex items-start gap-4 cursor-pointer group ${
                  !n.is_read ? 'bg-blue-50/20' : ''
                }`}
              >
                {style.icon}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={`font-bold text-dark text-xs ${!n.is_read ? 'text-primary' : ''}`}>
                      {n.title}
                    </span>
                    <span className={`px-2 py-0.2 rounded-full text-[9px] font-bold uppercase border ${style.badge}`}>
                      {n.priority}
                    </span>
                    <span className="px-2 py-0.2 rounded-full text-[9px] font-semibold bg-slate-100 text-slate-700 uppercase">
                      {n.category.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] text-slate-400 ml-auto">{n.time_ago}</span>
                  </div>

                  <p className="text-xs text-secondary leading-relaxed">{n.message}</p>
                </div>

                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => handleArchive(n.id, e)}
                    className="p-1 rounded text-secondary hover:text-dark hover:bg-slate-200"
                    title="Archive notification"
                  >
                    <Archive className="w-3.5 h-3.5" />
                  </button>
                  {n.link && <ArrowRight className="w-4 h-4 text-primary" />}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-secondary px-2">
          <span>
            Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of {total} notifications
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded border border-border bg-white text-dark disabled:opacity-40"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="font-semibold text-dark">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded border border-border bg-white text-dark disabled:opacity-40"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Notification Preferences Modal */}
      {showPreferences && preferences && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4 border border-border text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-sm font-bold text-dark">Notification Preferences</h3>
              <button
                onClick={() => setShowPreferences(false)}
                className="p-1 rounded text-secondary hover:text-dark hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {prefSuccess && (
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
                  <span>In-App Notifications (Bell & Toast)</span>
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
                  <span>Email Digest for Critical Alerts</span>
                </label>
              </div>

              <div className="space-y-2 pt-2 border-t border-border">
                <span className="font-bold text-dark block">Subscribed Categories</span>
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

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowPreferences(false)}
                  className="px-3 py-1.5 rounded-lg border border-border text-dark hover:bg-slate-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={prefSaving}
                  className="px-4 py-1.5 rounded-lg bg-primary text-white font-semibold hover:bg-primary-hover shadow-sm disabled:opacity-50"
                >
                  {prefSaving ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
