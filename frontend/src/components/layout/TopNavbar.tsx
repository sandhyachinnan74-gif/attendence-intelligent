import React, { useState } from 'react';
import { Search, Bell, LogOut, ShieldCheck, ChevronDown, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

interface TopNavbarProps {
  collapsed: boolean;
}

export const TopNavbar: React.FC<TopNavbarProps> = ({ collapsed }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
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
      {/* Left: Global Search & Engine Indicator */}
      <div className="flex items-center gap-4 flex-1 max-w-md">
        <div className="relative w-full">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
          <input
            type="text"
            placeholder="Search employees, shifts, policies..."
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-4">
        {/* Live Engine Status */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[11px] font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>Engine Active</span>
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-lg text-secondary hover:text-dark hover:bg-slate-100 transition-colors relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger"></span>
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-border rounded-xl shadow-lg py-2 z-50">
              <div className="px-4 py-2 border-b border-border flex items-center justify-between">
                <span className="text-xs font-semibold text-dark">Notifications</span>
                <span className="text-[10px] text-primary cursor-pointer hover:underline">Mark all read</span>
              </div>
              <div className="divide-y divide-border text-xs">
                <div className="px-4 py-3 hover:bg-slate-50 flex items-start gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-warning mt-1 flex-shrink-0"></div>
                  <div>
                    <p className="font-medium text-dark">Unusual Overtime Detected</p>
                    <p className="text-[11px] text-secondary">3 employees exceeded 3 hours overtime today.</p>
                    <span className="text-[9px] text-slate-400">10 mins ago</span>
                  </div>
                </div>
                <div className="px-4 py-3 hover:bg-slate-50 flex items-start gap-2.5">
                  <div className="w-2 h-2 rounded-full bg-success mt-1 flex-shrink-0"></div>
                  <div>
                    <p className="font-medium text-dark">Policy Document Processed</p>
                    <p className="text-[11px] text-secondary">Attendance Guidelines successfully indexed.</p>
                    <span className="text-[9px] text-slate-400">1 hour ago</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative">
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
                <p className="text-xs font-bold text-dark">{user?.email}</p>
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
