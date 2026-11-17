import React, { useState, useEffect, useRef } from 'react';
import {
  Search,
  Bell,
  LogOut,
  ChevronDown,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
  Clock,
  CalendarCheck,
  FileText,
  Users,
  Building,
  ArrowRight,
  X,
  ExternalLink
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../../services/api';

interface TopNavbarProps {
  collapsed: boolean;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({ collapsed }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Dropdown states
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  // Notifications state
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loadingNotifs, setLoadingNotifs] = useState(false);

  // Global Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);

  const searchContainerRef = useRef<HTMLDivElement>(null);
  const notifContainerRef = useRef<HTMLDivElement>(null);
  const profileContainerRef = useRef<HTMLDivElement>(null);

  // Fetch notifications count
  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/notifications/unread-count');
      setUnreadCount(res.data.unread_count || 0);
    } catch (e) {
      // Background silent failover
    }
  };

  const fetchRecentNotifications = async () => {
    setLoadingNotifs(true);
    try {
      const res = await api.get('/notifications?page=1&page_size=5');
      setNotifications(res.data.items || []);
      setUnreadCount(res.data.unread_count || 0);
    } catch (e) {
      console.error('Failed to load notifications:', e);
    } finally {
      setLoadingNotifs(false);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (showNotifications) {
      fetchRecentNotifications();
    }
  }, [showNotifications]);

  // Global search effect
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      setIsSearching(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.get(`/search?q=${encodeURIComponent(searchQuery.trim())}&limit=4`);
        setSearchResults(res.data);
        setShowSearchResults(true);
      } catch (e) {
        console.error('Global search failed:', e);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Close menus on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setShowSearchResults(false);
      }
      if (notifContainerRef.current && !notifContainerRef.current.contains(e.target as Node)) {
        setShowNotifications(false);
      }
      if (profileContainerRef.current && !profileContainerRef.current.contains(e.target as Node)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleMarkAsRead = async (id: string, link?: string) => {
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      setUnreadCount((c) => Math.max(0, c - 1));
      if (link) {
        setShowNotifications(false);
        navigate(link);
      }
    } catch (e) {
      console.error('Failed to mark notification as read:', e);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (e) {
      console.error('Failed to mark all as read:', e);
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <AlertCircle className="w-3.5 h-3.5 text-danger flex-shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="w-3.5 h-3.5 text-warning flex-shrink-0 mt-0.5" />;
      case 'success':
        return <CheckCircle2 className="w-3.5 h-3.5 text-success flex-shrink-0 mt-0.5" />;
      default:
        return <Info className="w-3.5 h-3.5 text-primary flex-shrink-0 mt-0.5" />;
    }
  };

  const roleBadgeColor = {
    admin: 'bg-purple-50 text-purple-700 border-purple-200',
    hr_manager: 'bg-blue-50 text-blue-700 border-blue-200',
    employee: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  }[user?.role || 'employee'];

  return (
    <header
      className={`fixed top-0 right-0 z-20 h-16 bg-white border-b border-border transition-all duration-300 flex items-center justify-between px-6 ${
        collapsed ? 'left-20' : 'left-64'
      }`}
    >
      {/* Left: Global Search with Role-Scoped Popover */}
      <div ref={searchContainerRef} className="relative flex-1 max-w-md">
        <div className="relative w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => {
              if (searchQuery.trim() && searchResults) setShowSearchResults(true);
            }}
            placeholder={
              user?.role === 'employee'
                ? 'Search my attendance, shifts, leave, policies...'
                : 'Search employees, departments, shifts, policies, anomalies...'
            }
            className="w-full pl-9 pr-8 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:bg-white transition-all shadow-xs"
          />
          {searchQuery && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSearchResults(null);
                setShowSearchResults(false);
              }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-dark p-0.5"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </div>

        {/* Global Search Results Popover */}
        {showSearchResults && searchResults && (
          <div className="absolute left-0 right-0 mt-2 bg-white border border-border rounded-xl shadow-xl max-h-96 overflow-y-auto z-50 divide-y divide-border text-xs">
            {searchResults.total_results === 0 ? (
              <div className="p-4 text-center text-secondary">
                No matching workforce records found for "{searchQuery}".
              </div>
            ) : (
              <>
                {/* Employees Group */}
                {searchResults.employees?.length > 0 && (
                  <div className="p-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-secondary px-2 py-1 block">
                      Employees & Profiles
                    </span>
                    {searchResults.employees.map((item: any) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setShowSearchResults(false);
                          setSearchQuery('');
                          navigate(item.link);
                        }}
                        className="px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between cursor-pointer transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-dark">{item.title}</p>
                          <p className="text-[11px] text-secondary">{item.subtitle}</p>
                        </div>
                        <span className="text-[10px] bg-blue-50 text-primary border border-blue-100 rounded px-1.5 py-0.5">
                          {item.tag}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Departments Group */}
                {searchResults.departments?.length > 0 && (
                  <div className="p-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-secondary px-2 py-1 block">
                      Departments
                    </span>
                    {searchResults.departments.map((item: any) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setShowSearchResults(false);
                          setSearchQuery('');
                          navigate(item.link);
                        }}
                        className="px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between cursor-pointer transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-dark">{item.title}</p>
                          <p className="text-[11px] text-secondary">{item.subtitle}</p>
                        </div>
                        <span className="text-[10px] bg-slate-100 text-slate-700 rounded px-1.5 py-0.5">
                          Department
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Shifts Group */}
                {searchResults.shifts?.length > 0 && (
                  <div className="p-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-secondary px-2 py-1 block">
                      Shifts & Schedules
                    </span>
                    {searchResults.shifts.map((item: any) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setShowSearchResults(false);
                          setSearchQuery('');
                          navigate(item.link);
                        }}
                        className="px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between cursor-pointer transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-dark">{item.title}</p>
                          <p className="text-[11px] text-secondary">{item.subtitle}</p>
                        </div>
                        <span className="text-[10px] bg-purple-50 text-purple-700 border border-purple-100 rounded px-1.5 py-0.5">
                          Shift
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Policies Group */}
                {searchResults.policies?.length > 0 && (
                  <div className="p-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-secondary px-2 py-1 block">
                      Policies & Documents
                    </span>
                    {searchResults.policies.map((item: any) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setShowSearchResults(false);
                          setSearchQuery('');
                          navigate(item.link);
                        }}
                        className="px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between cursor-pointer transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-dark">{item.title}</p>
                          <p className="text-[11px] text-secondary">{item.subtitle}</p>
                        </div>
                        <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-100 rounded px-1.5 py-0.5">
                          Policy
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Attendance Group */}
                {searchResults.attendance?.length > 0 && (
                  <div className="p-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-secondary px-2 py-1 block">
                      Attendance Records
                    </span>
                    {searchResults.attendance.map((item: any) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setShowSearchResults(false);
                          setSearchQuery('');
                          navigate(item.link);
                        }}
                        className="px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between cursor-pointer transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-dark">{item.title}</p>
                          <p className="text-[11px] text-secondary">{item.subtitle}</p>
                        </div>
                        <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-100 rounded px-1.5 py-0.5">
                          Attendance
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Leave Group */}
                {searchResults.leave?.length > 0 && (
                  <div className="p-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-secondary px-2 py-1 block">
                      Leave Records
                    </span>
                    {searchResults.leave.map((item: any) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setShowSearchResults(false);
                          setSearchQuery('');
                          navigate(item.link);
                        }}
                        className="px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between cursor-pointer transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-dark">{item.title}</p>
                          <p className="text-[11px] text-secondary">{item.subtitle}</p>
                        </div>
                        <span className="text-[10px] bg-teal-50 text-teal-700 border border-teal-100 rounded px-1.5 py-0.5">
                          Leave
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Anomalies Group (Admin & HR Only) */}
                {searchResults.anomalies?.length > 0 && (
                  <div className="p-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-secondary px-2 py-1 block">
                      Attendance Anomalies
                    </span>
                    {searchResults.anomalies.map((item: any) => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setShowSearchResults(false);
                          setSearchQuery('');
                          navigate(item.link);
                        }}
                        className="px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between cursor-pointer transition-colors"
                      >
                        <div>
                          <p className="font-semibold text-dark">{item.title}</p>
                          <p className="text-[11px] text-secondary">{item.subtitle}</p>
                        </div>
                        <span className="text-[10px] bg-red-50 text-danger border border-red-100 rounded px-1.5 py-0.5">
                          Anomaly
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Right Actions: Notification Center & User Profile */}
      <div className="flex items-center gap-3">
        {/* Event-Driven Notification Bell */}
        <div ref={notifContainerRef} className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-lg text-secondary hover:text-dark hover:bg-slate-100 transition-colors relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-danger text-white text-[9px] font-bold flex items-center justify-center animate-pulse">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-88 sm:w-96 bg-white border border-border rounded-xl shadow-xl py-2 z-50">
              <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-dark">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full bg-blue-100 text-primary text-[10px] font-semibold">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={handleMarkAllRead}
                    className="text-[11px] text-primary hover:underline font-medium"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="divide-y divide-border text-xs max-h-80 overflow-y-auto">
                {loadingNotifs ? (
                  <div className="p-4 text-center text-secondary">Loading notifications...</div>
                ) : notifications.length === 0 ? (
                  <div className="p-6 text-center text-secondary">
                    <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-1.5" />
                    <span>You're all caught up! No notifications.</span>
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => handleMarkAsRead(n.id, n.link)}
                      className={`px-4 py-3 hover:bg-slate-50/80 flex items-start gap-3 transition-colors cursor-pointer ${
                        !n.is_read ? 'bg-blue-50/30' : ''
                      }`}
                    >
                      {getPriorityIcon(n.priority)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1 mb-0.5">
                          <p className={`font-semibold text-dark truncate ${!n.is_read ? 'text-primary font-bold' : ''}`}>
                            {n.title}
                          </p>
                          <span className="text-[10px] text-slate-400 flex-shrink-0">{n.time_ago}</span>
                        </div>
                        <p className="text-[11px] text-secondary leading-snug">{n.message}</p>
                      </div>
                      {!n.is_read && (
                        <span className="w-2 h-2 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                      )}
                    </div>
                  ))
                )}
              </div>

              <div className="p-2 border-t border-border bg-slate-50/50 text-center">
                <Link
                  to="/notifications"
                  onClick={() => setShowNotifications(false)}
                  className="inline-flex items-center gap-1.5 text-xs text-primary font-semibold hover:underline"
                >
                  <span>Open Full Notification Center</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div ref={profileContainerRef} className="relative">
          <button
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-left"
          >
            <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-xs">
              {user?.first_name?.[0] || 'U'}
            </div>
            <div className="hidden sm:flex flex-col">
              <span className="text-xs font-semibold text-dark leading-tight">
                {user?.first_name} {user?.last_name}
              </span>
              <span className="text-[10px] text-secondary">{user?.organization_name || 'AttendAI'}</span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-secondary" />
          </button>

          {showProfileMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-border rounded-xl shadow-lg py-2 z-50">
              <div className="px-4 py-2 border-b border-border">
                <p className="text-xs font-bold text-dark truncate">{user?.email}</p>
                <div className="mt-1 flex items-center gap-1.5">
                  <span
                    className={`inline-block px-2 py-0.5 text-[10px] font-semibold rounded-full border capitalize ${roleBadgeColor}`}
                  >
                    {user?.role?.replace('_', ' ')}
                  </span>
                  {user?.employee_code && (
                    <span className="text-[10px] text-secondary">({user.employee_code})</span>
                  )}
                </div>
              </div>

              <div className="py-1 text-xs">
                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    navigate('/settings');
                  }}
                  className="w-full text-left px-4 py-2 hover:bg-slate-50 text-secondary hover:text-dark"
                >
                  Account Settings
                </button>
                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    navigate('/notifications');
                  }}
                  className="w-full text-left px-4 py-2 hover:bg-slate-50 text-secondary hover:text-dark flex items-center justify-between"
                >
                  <span>Notification Center</span>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.2 rounded-full bg-primary text-white text-[9px] font-bold">
                      {unreadCount}
                    </span>
                  )}
                </button>
              </div>

              <div className="pt-1 border-t border-border">
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-danger hover:bg-red-50 flex items-center gap-2 text-xs font-medium"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
