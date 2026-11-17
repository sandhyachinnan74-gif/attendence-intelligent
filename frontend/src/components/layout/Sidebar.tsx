import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building,
  Clock,
  CalendarDays,
  CalendarCheck,
  AlertTriangle,
  Bot,
  FileText,
  BarChart3,
  Settings,
  HelpCircle,
  Activity,
  History,
  UserCheck,
  User,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const { user } = useAuth();
  const role = user?.role || 'employee';

  let navGroups = [];

  if (role === 'admin') {
    navGroups = [
      {
        title: 'Workforce Management',
        items: [
          { name: 'Dashboard', to: '/', icon: LayoutDashboard },
          { name: 'Employees', to: '/employees', icon: Users },
          { name: 'Departments', to: '/departments', icon: Building },
          { name: 'Attendance', to: '/attendance', icon: Clock },
          { name: 'Shifts & Scheduling', to: '/shifts', icon: CalendarDays },
          { name: 'Leave Management', to: '/leave', icon: CalendarCheck },
        ],
      },
      {
        title: 'Intelligence & Analytics',
        items: [
          { name: 'Anomaly Detection', to: '/anomalies', icon: AlertTriangle },
          { name: 'AI Assistant', to: '/ai', icon: Bot },
          { name: 'Policies & Documents', to: '/policies', icon: FileText },
          { name: 'Analytics & Reports', to: '/analytics', icon: BarChart3 },
        ],
      },
      {
        title: 'System & Security',
        items: [
          { name: 'User Management', to: '/settings?tab=users', icon: UserCheck },
          { name: 'Settings', to: '/settings', icon: Settings },
          { name: 'System Diagnostics', to: '/diagnostics', icon: Activity },
          { name: 'Audit Logs', to: '/audit-logs', icon: History },
          { name: 'Help & Support', to: '/help', icon: HelpCircle },
        ],
      },
    ];
  } else if (role === 'hr_manager') {
    navGroups = [
      {
        title: 'HR Operations',
        items: [
          { name: 'Dashboard', to: '/', icon: LayoutDashboard },
          { name: 'Employees', to: '/employees', icon: Users },
          { name: 'Attendance', to: '/attendance', icon: Clock },
          { name: 'Shifts & Scheduling', to: '/shifts', icon: CalendarDays },
          { name: 'Leave Management', to: '/leave', icon: CalendarCheck },
        ],
      },
      {
        title: 'Intelligence & Reporting',
        items: [
          { name: 'Anomaly Detection', to: '/anomalies', icon: AlertTriangle },
          { name: 'AI Assistant', to: '/ai', icon: Bot },
          { name: 'Policies & Documents', to: '/policies', icon: FileText },
          { name: 'Analytics & Reports', to: '/analytics', icon: BarChart3 },
        ],
      },
      {
        title: 'Account',
        items: [
          { name: 'Personal Settings', to: '/settings', icon: Settings },
          { name: 'Help & Support', to: '/help', icon: HelpCircle },
        ],
      },
    ];
  } else {
    // Employee
    navGroups = [
      {
        title: 'My Workspace',
        items: [
          { name: 'My Dashboard', to: '/', icon: LayoutDashboard },
          { name: 'My Attendance', to: '/attendance', icon: Clock },
          { name: 'My Shifts', to: '/shifts', icon: CalendarDays },
          { name: 'My Leave', to: '/leave', icon: CalendarCheck },
        ],
      },
      {
        title: 'Knowledge & AI',
        items: [
          { name: 'AI Assistant', to: '/ai', icon: Bot },
          { name: 'Policies & Documents', to: '/policies', icon: FileText },
        ],
      },
      {
        title: 'Personal',
        items: [
          { name: 'My Profile', to: '/settings?tab=profile', icon: User },
          { name: 'Settings', to: '/settings', icon: Settings },
          { name: 'Help & Support', to: '/help', icon: HelpCircle },
        ],
      },
    ];
  }

  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen transition-all duration-300 bg-sidebar border-r border-border flex flex-col ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-border">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-white flex-shrink-0 shadow-sm">
            <Clock className="w-5 h-5" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-dark text-lg leading-tight tracking-tight">AttendAI</span>
              <span className="text-[10px] text-secondary font-medium tracking-wide">Intelligent Workforce</span>
            </div>
          )}
        </div>
        <button
          onClick={onToggle}
          className="p-1 rounded-md text-secondary hover:text-dark hover:bg-slate-200/60 transition-colors"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
        {navGroups.map((group, idx) => (
          <div key={idx}>
            {!collapsed && (
              <h3 className="px-3 mb-2 text-[11px] font-semibold text-secondary uppercase tracking-wider">
                {group.title}
              </h3>
            )}
            <nav className="space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-primary text-white shadow-sm'
                          : 'text-secondary hover:text-dark hover:bg-slate-200/50'
                      } ${collapsed ? 'justify-center' : ''}`
                    }
                    title={collapsed ? item.name : undefined}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    {!collapsed && <span>{item.name}</span>}
                  </NavLink>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* User Footer Summary */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-3 p-2 rounded-lg bg-white/70 border border-border/60">
          <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center flex-shrink-0 text-xs">
            {user?.first_name?.[0] || 'U'}
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-semibold text-dark truncate">
                {user?.first_name} {user?.last_name}
              </span>
              <span className="text-[10px] text-secondary capitalize">{user?.role?.replace('_', ' ')}</span>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
