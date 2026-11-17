import React, { useEffect, useState } from 'react';
import {
  Users,
  UserCheck,
  UserX,
  ClockAlert,
  Clock,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Download,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  Play,
  Square,
  Coffee,
  CalendarCheck,
  CheckCircle2,
  FileText,
  Bot
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';
import { api } from '../services/api';
import { DashboardData, AttendanceRecord } from '../types';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { LiveClock } from '../components/common/LiveClock';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  // Employee Portal State
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [myRecords, setMyRecords] = useState<AttendanceRecord[]>([]);
  const [clockActionLoading, setClockActionLoading] = useState(false);

  const fetchEmployeeData = async () => {
    setLoading(true);
    try {
      const [todayRes, listRes] = await Promise.all([
        api.get('/attendance/today').catch(() => ({ data: null })),
        api.get('/attendance?limit=5').catch(() => ({ data: [] })),
      ]);
      setTodayRecord(todayRes.data);
      setMyRecords(listRes.data || []);
    } catch (e) {
      console.error('Failed to load employee data:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchAdminDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.get('/analytics/dashboard');
      setData(res.data);
    } catch (e) {
      console.error('Failed to load dashboard metrics:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'employee') {
      fetchEmployeeData();
    } else {
      fetchAdminDashboard();
    }
  }, [user]);

  const handleClockIn = async () => {
    setClockActionLoading(true);
    try {
      await api.post('/attendance/clock-in', {});
      await fetchEmployeeData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to clock in');
    } finally {
      setClockActionLoading(false);
    }
  };

  const handleClockOut = async () => {
    setClockActionLoading(true);
    try {
      await api.post('/attendance/clock-out', {});
      await fetchEmployeeData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to clock out');
    } finally {
      setClockActionLoading(false);
    }
  };

  const handleToggleBreak = async () => {
    setClockActionLoading(true);
    try {
      await api.post('/attendance/break', { reason: 'Break' });
      await fetchEmployeeData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to toggle break');
    } finally {
      setClockActionLoading(false);
    }
  };

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  // -------------------------------------------------------------
  // EMPLOYEE PERSONAL WORKFORCE PORTAL
  // -------------------------------------------------------------
  if (user?.role === 'employee') {
    const isClockedIn = !!todayRecord?.clock_in && !todayRecord?.clock_out;
    const isClockedOut = !!todayRecord?.clock_in && !!todayRecord?.clock_out;
    const hasOpenBreak = todayRecord?.breaks?.some((b) => !b.break_end);

    const totalWorkedHrs = myRecords.reduce((acc, r) => acc + (r.worked_minutes || 0) / 60, 0);

    return (
      <div className="space-y-6">
        {/* Welcome Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <h1 className="text-xl font-bold text-dark tracking-tight">
              Welcome back, {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : (user?.email || 'Employee')}
            </h1>
            <p className="text-xs text-secondary mt-0.5">
              Personal Workforce Portal &bull; {user?.employee_code || 'EMP'} &bull; {todayStr}
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchEmployeeData}
              disabled={loading}
              className="px-3 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-50 flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-primary' : 'text-secondary'}`} />
              <span>Refresh</span>
            </button>
            <Link
              to="/leave"
              className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary-hover flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <CalendarCheck className="w-3.5 h-3.5" />
              <span>Request Leave</span>
            </Link>
          </div>
        </div>

        {/* Live Clock & Action Banner */}
        <div className="bg-gradient-to-r from-blue-900 to-indigo-900 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <span className="inline-block px-3 py-0.5 rounded-full text-[11px] font-semibold bg-white/10 border border-white/20 uppercase tracking-wider text-blue-200">
              Shift: General (09:00 - 17:00)
            </span>
            <LiveClock className="text-3xl sm:text-4xl font-extrabold tracking-tight font-mono text-white" />
            <p className="text-xs text-blue-200">
              Status:{' '}
              <span className="font-bold text-white uppercase">
                {isClockedOut
                  ? 'Shift Completed'
                  : hasOpenBreak
                  ? 'On Break'
                  : isClockedIn
                  ? 'Actively Working'
                  : 'Not Clocked In'}
              </span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {!isClockedIn && !isClockedOut && (
              <button
                onClick={handleClockIn}
                disabled={clockActionLoading}
                className="px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-xs flex items-center gap-2 shadow-lg transition-all transform active:scale-95 disabled:opacity-50"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>Clock In Now</span>
              </button>
            )}

            {isClockedIn && (
              <>
                <button
                  onClick={handleToggleBreak}
                  disabled={clockActionLoading}
                  className={`px-4 py-3 rounded-xl text-white font-semibold text-xs flex items-center gap-2 shadow-md transition-all ${
                    hasOpenBreak ? 'bg-amber-500 hover:bg-amber-600' : 'bg-slate-700 hover:bg-slate-800'
                  }`}
                >
                  <Coffee className="w-4 h-4" />
                  <span>{hasOpenBreak ? 'End Break' : 'Start Break'}</span>
                </button>

                <button
                  onClick={handleClockOut}
                  disabled={clockActionLoading || hasOpenBreak}
                  className="px-5 py-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs flex items-center gap-2 shadow-lg transition-all transform active:scale-95 disabled:opacity-50"
                >
                  <Square className="w-4 h-4 fill-white" />
                  <span>Clock Out</span>
                </button>
              </>
            )}

            {isClockedOut && (
              <div className="px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Completed for Today</span>
              </div>
            )}
          </div>
        </div>

        {/* Employee Summary KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Hours Logged
            </span>
            <div className="text-2xl font-bold text-dark">{totalWorkedHrs.toFixed(1)}h</div>
            <span className="text-[10px] text-secondary">Past 5 shifts</span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Recent Punctuality
            </span>
            <div className="text-2xl font-bold text-success">
              {myRecords.length > 0
                ? `${Math.round(
                    (myRecords.filter((r) => r.status === 'present').length / myRecords.length) * 100
                  )}%`
                : '100%'}
            </div>
            <span className="text-[10px] text-secondary">On-time arrival</span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Overtime
            </span>
            <div className="text-2xl font-bold text-primary">
              {(myRecords.reduce((acc, r) => acc + (r.overtime_minutes || 0), 0) / 60).toFixed(1)}h
            </div>
            <span className="text-[10px] text-secondary">Approved overtime</span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Leave Balance
            </span>
            <div className="text-2xl font-bold text-dark">18 Days</div>
            <span className="text-[10px] text-secondary">Paid time off</span>
          </div>
        </div>

        {/* Quick Help & AI Assistant Card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-card border border-border rounded-xl p-5 shadow-card flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-primary flex items-center justify-center flex-shrink-0">
              <Bot className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-xs font-bold text-dark">AttendAI Personal Assistant</h3>
              <p className="text-xs text-secondary">
                Ask questions about your working hours, shift schedule, overtime policies, or leave rules.
              </p>
              <Link to="/ai" className="inline-block text-xs font-semibold text-primary hover:underline pt-1">
                Chat with Assistant &rarr;
              </Link>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-card flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-success flex items-center justify-center flex-shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-xs font-bold text-dark">HR Policy & Handbook</h3>
              <p className="text-xs text-secondary">
                Search official company policies on remote work, overtime compensation, breaks, and compliance.
              </p>
              <Link to="/policies" className="inline-block text-xs font-semibold text-success hover:underline pt-1">
                Browse Policies &rarr;
              </Link>
            </div>
          </div>
        </div>

        {/* Recent Personal Attendance */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-dark">Recent Personal Attendance</h2>
            <Link to="/attendance" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              <span>View Full History</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-secondary uppercase tracking-wider text-[10px]">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Clock In</th>
                  <th className="py-2.5 px-3">Clock Out</th>
                  <th className="py-2.5 px-3">Worked Duration</th>
                  <th className="py-2.5 px-3">Overtime</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-medium">
                {myRecords.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-2.5 px-3 font-semibold text-dark">{r.date}</td>
                    <td className="py-2.5 px-3 text-dark font-mono">
                      {r.clock_in ? new Date(r.clock_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-dark font-mono">
                      {r.clock_out ? new Date(r.clock_out).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                    <td className="py-2.5 px-3 text-dark font-mono">
                      {((r.worked_minutes || 0) / 60).toFixed(1)}h
                    </td>
                    <td className="py-2.5 px-3 text-secondary font-mono">
                      {((r.overtime_minutes || 0) / 60).toFixed(1)}h
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded-full capitalize ${
                          r.status === 'present'
                            ? 'bg-emerald-50 text-success'
                            : r.status === 'late'
                            ? 'bg-amber-50 text-warning'
                            : r.status === 'incomplete'
                            ? 'bg-slate-100 text-secondary'
                            : 'bg-rose-50 text-danger'
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // ADMIN / HR WORKFORCE DASHBOARD
  // -------------------------------------------------------------
  const kpis = data?.kpis;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Workforce Dashboard</h1>
          <p className="text-xs text-secondary mt-0.5">Real-time attendance intelligence &bull; {todayStr}</p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchAdminDashboard}
            disabled={loading}
            className="px-3 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-50 flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-primary' : 'text-secondary'}`} />
            <span>Refresh</span>
          </button>
          <a
            href="/api/v1/exports/attendance/csv"
            download
            className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary-hover flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total Employees */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Employees</span>
            <div className="w-7 h-7 rounded-lg bg-blue-50 text-primary flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.total_employees || 0}</span>
            <div className="flex items-center gap-1 text-[11px] text-secondary mt-1 font-medium">
              <span>Active headcount</span>
            </div>
          </div>
        </div>

        {/* Present Today */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Present</span>
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-success flex items-center justify-center">
              <UserCheck className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.present_today || 0}</span>
            <div className="flex items-center gap-1 text-[11px] text-success mt-1 font-medium">
              <TrendingUp className="w-3 h-3" />
              <span>+{kpis?.comparison?.present || 0}% vs yest</span>
            </div>
          </div>
        </div>

        {/* Absent Today */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Absent</span>
            <div className="w-7 h-7 rounded-lg bg-rose-50 text-danger flex items-center justify-center">
              <UserX className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.absent_today || 0}</span>
            <div className="flex items-center gap-1 text-[11px] text-secondary mt-1 font-medium">
              <span>Unscheduled leaves</span>
            </div>
          </div>
        </div>

        {/* Late Arrivals */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Late Arrivals</span>
            <div className="w-7 h-7 rounded-lg bg-amber-50 text-warning flex items-center justify-center">
              <ClockAlert className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.late_arrivals || 0}</span>
            <div className="flex items-center gap-1 text-[11px] text-warning mt-1 font-medium">
              <TrendingDown className="w-3 h-3" />
              <span>{kpis?.comparison?.late || 0}% change</span>
            </div>
          </div>
        </div>

        {/* Overtime Hours */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Overtime</span>
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-primary flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.overtime_hours || 0}h</span>
            <div className="flex items-center gap-1 text-[11px] text-secondary mt-1 font-medium">
              <span>Recorded today</span>
            </div>
          </div>
        </div>

        {/* Punctuality Rate */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Attendance Rate</span>
            <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.attendance_rate || 0}%</span>
            <div className="flex items-center gap-1 text-[11px] text-success mt-1 font-medium">
              <span>Healthy threshold</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attendance Trends Area Chart */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-dark">Attendance & Late Trends</h2>
              <p className="text-[11px] text-secondary">Past 7 business days trajectory</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5 text-secondary">
                <span className="w-2.5 h-2.5 rounded-full bg-primary"></span>
                Present
              </span>
              <span className="flex items-center gap-1.5 text-secondary">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>
                Late
              </span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.trends || []}>
                <defs>
                  <linearGradient id="colorPresent" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorLate" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Area type="monotone" dataKey="present" stroke="#2563EB" strokeWidth={2} fillOpacity={1} fill="url(#colorPresent)" />
                <Area type="monotone" dataKey="late" stroke="#F59E0B" strokeWidth={2} fillOpacity={1} fill="url(#colorLate)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Department Attendance Rate Bar Chart */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card">
          <h2 className="text-sm font-bold text-dark mb-1">Department Rates</h2>
          <p className="text-[11px] text-secondary mb-4">Attendance percentage by business unit</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.department_stats || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <YAxis dataKey="department" type="category" tick={{ fontSize: 10, fill: '#111827' }} width={80} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'Rate']}
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="rate" fill="#2563EB" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Needs Attention & AI Insights Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Needs Attention */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" />
              <h2 className="text-sm font-bold text-dark">Needs Attention</h2>
            </div>
            <Link to="/anomalies" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="divide-y divide-border">
            {data?.needs_attention && data.needs_attention.length > 0 ? (
              data.needs_attention.map((item) => (
                <div key={item.id} className="py-3 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-dark">{item.employee}</span>
                      <span className="text-[10px] text-secondary font-mono">{item.date}</span>
                      <span
                        className={`px-2 py-0.5 text-[9px] font-bold uppercase rounded-full border ${
                          item.severity === 'critical'
                            ? 'bg-rose-50 text-danger border-rose-200'
                            : item.severity === 'high'
                            ? 'bg-amber-50 text-warning border-amber-200'
                            : 'bg-blue-50 text-primary border-blue-200'
                        }`}
                      >
                        {item.severity}
                      </span>
                    </div>
                    <p className="text-xs text-secondary">{item.explanation}</p>
                  </div>
                  <Link
                    to="/anomalies"
                    className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 border border-border text-[11px] font-medium text-dark rounded-md flex-shrink-0"
                  >
                    Investigate
                  </Link>
                </div>
              ))
            ) : (
              <p className="text-xs text-secondary py-6 text-center">No urgent anomalies pending review.</p>
            )}
          </div>
        </div>

        {/* AI Workforce Insights */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-6 h-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <h2 className="text-sm font-bold text-dark">AI Workforce Insights</h2>
          </div>

          <div className="space-y-3">
            {data?.ai_insights?.map((ins, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-border/80 space-y-1">
                <span className="text-xs font-semibold text-dark flex items-center gap-1.5">
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      ins.level === 'positive' ? 'bg-success' : ins.level === 'warning' ? 'bg-warning' : 'bg-primary'
                    }`}
                  ></span>
                  {ins.title}
                </span>
                <p className="text-xs text-secondary leading-relaxed">{ins.insight}</p>
              </div>
            ))}

            <Link
              to="/ai"
              className="mt-3 block text-center py-2 px-3 bg-primary/10 hover:bg-primary/20 text-primary font-semibold text-xs rounded-lg transition-colors"
            >
              Ask AttendAI Assistant &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-dark">Recent Activity</h2>
          <Link to="/attendance" className="text-xs font-semibold text-primary hover:underline flex items-center gap-1">
            <span>View Attendance Sheet</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border text-secondary uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-3">Employee</th>
                <th className="py-2.5 px-3">Department</th>
                <th className="py-2.5 px-3">Clock In</th>
                <th className="py-2.5 px-3">Clock Out</th>
                <th className="py-2.5 px-3">Worked Duration</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-medium">
              {data?.recent_activity?.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-dark">{r.employee}</td>
                  <td className="py-2.5 px-3 text-secondary">{r.department}</td>
                  <td className="py-2.5 px-3 text-dark font-mono">{r.clock_in}</td>
                  <td className="py-2.5 px-3 text-dark font-mono">{r.clock_out}</td>
                  <td className="py-2.5 px-3 text-dark font-mono">{r.worked_hours}h</td>
                  <td className="py-2.5 px-3">
                    <span
                      className={`inline-block px-2 py-0.5 text-[10px] font-bold rounded-full capitalize ${
                        r.status === 'present'
                          ? 'bg-emerald-50 text-success'
                          : r.status === 'late'
                          ? 'bg-amber-50 text-warning'
                          : r.status === 'incomplete'
                          ? 'bg-slate-100 text-secondary'
                          : 'bg-rose-50 text-danger'
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
