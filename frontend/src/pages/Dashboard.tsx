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
  Bot,
  Building,
  Calendar,
  CalendarDays,
  AlertCircle,
  HelpCircle,
  Check,
  X
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
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { api } from '../services/api';
import { DashboardData, AttendanceRecord } from '../types';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { LiveClock } from '../components/common/LiveClock';
import { downloadFile } from '../utils/download';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [adminData, setAdminData] = useState<any | null>(null);
  const [employeeData, setEmployeeData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [clockActionLoading, setClockActionLoading] = useState(false);

  // Leave request modal state (for employees)
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [leaveType, setLeaveType] = useState('annual');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [leaveReason, setLeaveReason] = useState('');
  const [leaveSubmitting, setLeaveSubmitting] = useState(false);
  const [leaveMsg, setLeaveMsg] = useState<{ text: string; error: boolean } | null>(null);

  const fetchAdminDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.get('/analytics/dashboard');
      setAdminData(res.data);
    } catch (e) {
      console.error('Failed to load dashboard metrics:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployeeDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.get('/analytics/employee-dashboard');
      setEmployeeData(res.data);
    } catch (e) {
      console.error('Failed to load employee dashboard:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'employee') {
      fetchEmployeeDashboard();
    } else {
      fetchAdminDashboard();
    }
  }, [user]);

  // Employee Punch Actions
  const handleClockIn = async () => {
    setClockActionLoading(true);
    try {
      await api.post('/attendance/clock-in', {});
      await fetchEmployeeDashboard();
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
      await fetchEmployeeDashboard();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to clock out');
    } finally {
      setClockActionLoading(false);
    }
  };

  const handleToggleBreak = async () => {
    setClockActionLoading(true);
    const hasOpenBreak = employeeData?.today_record?.has_open_break;
    try {
      if (hasOpenBreak) {
        await api.post('/attendance/end-break', {});
      } else {
        await api.post('/attendance/start-break', { reason: 'Lunch Break' });
      }
      await fetchEmployeeDashboard();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update break status');
    } finally {
      setClockActionLoading(false);
    }
  };

  // Leave Submit
  const handleApplyLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    setLeaveSubmitting(true);
    setLeaveMsg(null);
    try {
      await api.post('/leave', {
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        reason: leaveReason
      });
      setLeaveMsg({ text: 'Leave application submitted successfully.', error: false });
      setTimeout(() => {
        setShowLeaveModal(false);
        setLeaveMsg(null);
        fetchEmployeeDashboard();
      }, 1200);
    } catch (err: any) {
      setLeaveMsg({ text: err.response?.data?.detail || 'Failed to submit leave request.', error: true });
    } finally {
      setLeaveSubmitting(false);
    }
  };

  // HR Leave Quick Decision
  const handleLeaveDecision = async (leaveId: string, decision: 'approved' | 'rejected') => {
    try {
      await api.patch(`/leave/${leaveId}/review`, { status: decision });
      await fetchAdminDashboard();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to update leave request');
    }
  };

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  // -------------------------------------------------------------------------
  // RENDER: EMPLOYEE DASHBOARD
  // -------------------------------------------------------------------------
  if (user?.role === 'employee') {
    const kpis = employeeData?.kpis || {};
    const todayRec = employeeData?.today_record;
    const shift = employeeData?.assigned_shift;
    const punches = employeeData?.recent_punches || [];
    const trends = employeeData?.attendance_trends || [];
    const announcements = employeeData?.company_announcements || [];
    const leaveSummary = employeeData?.leave_summary || {};

    const isClockedIn = Boolean(todayRec?.clock_in);
    const isClockedOut = Boolean(todayRec?.clock_out);
    const hasOpenBreak = Boolean(todayRec?.has_open_break);

    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
          <div>
            <h1 className="text-xl font-bold text-dark tracking-tight">
              Welcome back, {user.first_name}!
            </h1>
            <p className="text-xs text-secondary mt-0.5">
              Personal Workforce Portal &bull; Shift: {shift?.name || 'General'} &bull; {todayStr}
            </p>
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={fetchEmployeeDashboard}
              disabled={loading}
              className="px-3 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-50 flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-primary' : 'text-secondary'}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => setShowLeaveModal(true)}
              className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary-hover flex items-center gap-1.5 transition-colors shadow-sm"
            >
              <CalendarCheck className="w-3.5 h-3.5" />
              <span>Apply for Leave</span>
            </button>
          </div>
        </div>

        {/* 1. Live Attendance Clock & Punch Banner */}
        <div className="bg-gradient-to-r from-blue-900 to-indigo-900 rounded-2xl p-6 text-white shadow-md flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <span className="inline-block px-3 py-0.5 rounded-full text-[11px] font-semibold bg-white/10 border border-white/20 uppercase tracking-wider text-blue-200">
              Shift: {shift?.name} ({shift?.start_time} - {shift?.end_time})
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

        {/* 2. Employee 6 KPI Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Today's Status
            </span>
            <div className="text-base font-bold text-dark capitalize truncate">
              {kpis.today_status?.replace('_', ' ') || 'Not Clocked'}
            </div>
            <span className="text-[10px] text-secondary">
              {todayRec?.clock_in ? `In: ${todayRec.clock_in}` : 'Shift pending'}
            </span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Hours Worked Today
            </span>
            <div className="text-2xl font-bold text-dark">{kpis.hours_worked_today || 0}h</div>
            <span className="text-[10px] text-secondary">Required: {shift?.required_hours || 8}h</span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Monthly Hours
            </span>
            <div className="text-2xl font-bold text-dark">{kpis.monthly_working_hours || 0}h</div>
            <span className="text-[10px] text-success font-medium">Logged this month</span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Monthly Overtime
            </span>
            <div className="text-2xl font-bold text-dark">{kpis.monthly_overtime || 0}h</div>
            <span className="text-[10px] text-secondary">Beyond scheduled shifts</span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Late Arrivals
            </span>
            <div className="text-2xl font-bold text-dark">{kpis.late_arrivals_this_month || 0}</div>
            <span className="text-[10px] text-secondary">Past shift grace period</span>
          </div>

          <div className="bg-card border border-border rounded-xl p-4 shadow-card">
            <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
              Leave Balance
            </span>
            <div className="text-2xl font-bold text-primary">{kpis.available_leave_balance || 0}d</div>
            <span className="text-[10px] text-secondary">Paid Time Off remaining</span>
          </div>
        </div>

        {/* 3. My Schedule & My Working Hours Trends */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* My Schedule Card */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <CalendarDays className="w-4 h-4 text-primary" />
                <h2 className="text-xs font-bold text-dark">My Schedule & Shift</h2>
              </div>
              <span className="text-[10px] font-semibold bg-blue-50 text-primary px-2 py-0.5 rounded border border-blue-100">
                Active Schedule
              </span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block font-medium">Assigned Shift</span>
                <span className="font-bold text-dark text-sm block mt-0.5">
                  {shift?.name || 'General Standard Shift'} {shift?.code ? `(${shift.code})` : ''}
                </span>
                <span className="text-secondary mt-1 block">
                  Working hours: <strong>{shift?.start_time || '09:00'} – {shift?.end_time || '17:00'}</strong> ({shift?.required_hours || 8.0}h required)
                </span>
              </div>

              <div className="p-3 bg-slate-50 border border-border rounded-lg flex items-center justify-between">
                <div>
                  <span className="text-secondary block font-medium">Punctuality Grace Period</span>
                  <span className="font-semibold text-dark text-xs block mt-0.5">
                    {shift?.grace_period_minutes ?? 15} minutes from shift start
                  </span>
                </div>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>

              <div className="p-3 bg-slate-50 border border-border rounded-lg">
                <span className="text-secondary block font-medium">Next Scheduled Days</span>
                <span className="font-semibold text-dark text-xs block mt-0.5">
                  Monday – Friday &bull; Standard Operating Hours
                </span>
              </div>
            </div>
          </div>

          {/* My Attendance Trends Chart */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-card lg:col-span-2">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
              <div>
                <h2 className="text-xs font-bold text-dark">My Attendance Trends (Past 7 Days)</h2>
                <p className="text-[11px] text-secondary mt-0.5">Worked hours vs standard 8-hour requirement</p>
              </div>
            </div>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="empHrsGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563EB" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#2563EB" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} stroke="#CBD5E1" />
                  <YAxis tick={{ fontSize: 10, fill: '#64748B' }} stroke="#CBD5E1" domain={[0, 12]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderRadius: '8px',
                      border: '1px solid #E2E8F0',
                      fontSize: '11px',
                    }}
                  />
                  <Area type="monotone" dataKey="hours" name="Worked Hours" stroke="#2563EB" fill="url(#empHrsGradient)" strokeWidth={2} />
                  <Area type="monotone" dataKey="required" name="Required (8h)" stroke="#94A3B8" strokeDasharray="3 3" fill="none" strokeWidth={1.5} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* 4. Recent Activity & Company Announcements */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Personal Punches */}
          <div className="bg-card border border-border rounded-xl p-5 shadow-card lg:col-span-2">
            <div className="flex items-center justify-between pb-3 border-b border-border mb-3">
              <h2 className="text-xs font-bold text-dark">Recent Attendance Punches</h2>
              <Link to="/attendance" className="text-[11px] text-primary hover:underline font-medium">
                View all history &rarr;
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border text-secondary text-[11px]">
                    <th className="pb-2 font-semibold">Date</th>
                    <th className="pb-2 font-semibold">Clock In</th>
                    <th className="pb-2 font-semibold">Clock Out</th>
                    <th className="pb-2 font-semibold">Worked</th>
                    <th className="pb-2 font-semibold">Overtime</th>
                    <th className="pb-2 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {punches.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-4 text-center text-secondary">
                        No previous punches found.
                      </td>
                    </tr>
                  ) : (
                    punches.map((p: any) => (
                      <tr key={p.id} className="hover:bg-slate-50/50">
                        <td className="py-2.5 font-medium text-dark">{p.date}</td>
                        <td className="py-2.5 text-secondary">{p.clock_in}</td>
                        <td className="py-2.5 text-secondary">{p.clock_out}</td>
                        <td className="py-2.5 font-semibold text-dark">{p.worked_hours}h</td>
                        <td className="py-2.5 text-secondary">
                          {p.overtime_hours > 0 ? (
                            <span className="font-semibold text-primary">+{p.overtime_hours}h</span>
                          ) : (
                            '0h'
                          )}
                        </td>
                        <td className="py-2.5">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize ${
                              p.status === 'present'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : p.status === 'late'
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Company Announcements & AI Assistant Shortcuts */}
          <div className="space-y-6">
            <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <FileText className="w-4 h-4 text-primary" />
                <h2 className="text-xs font-bold text-dark">Company Announcements</h2>
              </div>
              <div className="space-y-2.5 text-xs">
                {announcements.map((a: any) => (
                  <div key={a.id} className="p-3 bg-slate-50 border border-border rounded-lg space-y-1">
                    <p className="font-bold text-dark">{a.title}</p>
                    <p className="text-[11px] text-secondary leading-snug">{a.message}</p>
                    <span className="text-[9px] text-slate-400 block pt-1">{a.date}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Assistant Quick Card */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 shadow-card space-y-3">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-primary" />
                <h3 className="text-xs font-bold text-dark">AI Workforce Assistant</h3>
              </div>
              <p className="text-[11px] text-secondary leading-snug">
                Ask questions about your working hours, overtime balance, or attendance policies.
              </p>
              <div className="space-y-1.5 pt-1">
                <button
                  onClick={() => navigate('/ai')}
                  className="w-full text-left p-2 rounded bg-white border border-blue-200 text-[11px] font-medium text-dark hover:border-primary transition-colors flex items-center justify-between"
                >
                  <span>"How much overtime did I do this month?"</span>
                  <ArrowRight className="w-3 h-3 text-primary" />
                </button>
                <button
                  onClick={() => navigate('/ai')}
                  className="w-full text-left p-2 rounded bg-white border border-blue-200 text-[11px] font-medium text-dark hover:border-primary transition-colors flex items-center justify-between"
                >
                  <span>"What is our grace period policy?"</span>
                  <ArrowRight className="w-3 h-3 text-primary" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Leave Request Modal */}
        {showLeaveModal && (
          <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4 border border-border">
              <div className="flex items-center justify-between pb-3 border-b border-border">
                <h3 className="text-sm font-bold text-dark">Apply for Leave</h3>
                <button
                  onClick={() => setShowLeaveModal(false)}
                  className="p-1 rounded text-secondary hover:text-dark hover:bg-slate-100"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {leaveMsg && (
                <div
                  className={`p-3 rounded-lg text-xs border ${
                    leaveMsg.error ? 'bg-red-50 text-danger border-red-200' : 'bg-emerald-50 text-success border-emerald-200'
                  }`}
                >
                  {leaveMsg.text}
                </div>
              )}

              <form onSubmit={handleApplyLeave} className="space-y-3 text-xs">
                <div>
                  <label className="block font-medium text-dark mb-1">Leave Type</label>
                  <select
                    value={leaveType}
                    onChange={(e) => setLeaveType(e.target.value)}
                    className="w-full px-3 py-1.5 border border-border rounded-lg bg-slate-50 text-dark"
                  >
                    <option value="annual">Annual Leave (PTO)</option>
                    <option value="sick">Sick Leave</option>
                    <option value="casual">Casual Leave</option>
                    <option value="unpaid">Unpaid Leave</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-dark mb-1">Start Date</label>
                    <input
                      type="date"
                      required
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-1.5 border border-border rounded-lg bg-slate-50 text-dark"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-dark mb-1">End Date</label>
                    <input
                      type="date"
                      required
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-1.5 border border-border rounded-lg bg-slate-50 text-dark"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-dark mb-1">Reason for Leave</label>
                  <textarea
                    required
                    rows={3}
                    value={leaveReason}
                    onChange={(e) => setLeaveReason(e.target.value)}
                    placeholder="Brief explanation for time off..."
                    className="w-full px-3 py-1.5 border border-border rounded-lg bg-slate-50 text-dark"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                  <button
                    type="button"
                    onClick={() => setShowLeaveModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-border text-dark hover:bg-slate-50 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={leaveSubmitting}
                    className="px-4 py-1.5 rounded-lg bg-primary text-white font-semibold hover:bg-primary-hover shadow-sm disabled:opacity-50"
                  >
                    {leaveSubmitting ? 'Submitting...' : 'Submit Leave Request'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // RENDER: HR MANAGER & ADMIN DASHBOARD
  // -------------------------------------------------------------------------
  const isAdmin = user?.role === 'admin';
  const kpis = adminData?.kpis || {};
  const trends = adminData?.trends || [];
  const deptStats = adminData?.department_stats || [];
  const needsAttention = adminData?.needs_attention || [];
  const recentActivity = adminData?.recent_activity || [];
  const aiInsights = adminData?.ai_insights || [];
  const leaveDist = adminData?.leave_distribution || [];
  const overtimeDist = adminData?.overtime_distribution || [];
  const absenteeismTrends = adminData?.absenteeism_trends || [];
  const shiftOverview = adminData?.shift_overview || [];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">
            Workforce Dashboard
          </h1>
          <p className="text-xs text-secondary mt-0.5">
            {isAdmin
              ? `Executive organization-wide intelligence \u2022 ${todayStr}`
              : `HR Operational Overview & authorized monitoring \u2022 ${todayStr}`}
          </p>
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
          <button
            onClick={() => downloadFile('/exports/attendance/csv', 'attendai_attendance.csv')}
            className="px-3 py-1.5 bg-primary text-white rounded-lg text-xs font-medium hover:bg-primary-hover flex items-center gap-1.5 transition-colors shadow-sm cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* 8 KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        {/* Total Employees */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">
              {isAdmin ? 'Employees' : 'In Scope'}
            </span>
            <Users className="w-3.5 h-3.5 text-primary" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.total_employees || 0}</span>
            <span className="text-[9px] text-secondary block mt-0.5">Active headcount</span>
          </div>
        </div>

        {/* Present Today */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Present</span>
            <UserCheck className="w-3.5 h-3.5 text-success" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.present_today || 0}</span>
            <span className="text-[9px] text-success font-medium block mt-0.5">
              +{kpis.comparison?.present || 0}% vs yest
            </span>
          </div>
        </div>

        {/* Absent Today */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Absent</span>
            <UserX className="w-3.5 h-3.5 text-danger" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.absent_today || 0}</span>
            <span className="text-[9px] text-secondary block mt-0.5">Unexcused</span>
          </div>
        </div>

        {/* Late Arrivals */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Late Arrivals</span>
            <ClockAlert className="w-3.5 h-3.5 text-warning" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.late_arrivals || 0}</span>
            <span className="text-[9px] text-secondary block mt-0.5">Past grace period</span>
          </div>
        </div>

        {/* Employees on Leave / Pending Leave */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">On Leave</span>
            <Calendar className="w-3.5 h-3.5 text-purple-600" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.employees_on_leave || 0}</span>
            <span className="text-[9px] text-secondary block mt-0.5">Approved today</span>
          </div>
        </div>

        {/* Pending Approvals / Corrections */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Pending Action</span>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.pending_approvals || 0}</span>
            <span className="text-[9px] text-amber-600 font-medium block mt-0.5">Requires Review</span>
          </div>
        </div>

        {/* Total Overtime */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Overtime</span>
            <Clock className="w-3.5 h-3.5 text-primary" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.overtime_hours || 0}h</span>
            <span className="text-[9px] text-secondary block mt-0.5">Logged today</span>
          </div>
        </div>

        {/* Attendance Rate */}
        <div className="bg-card border border-border rounded-xl p-3 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider">Attendance %</span>
            <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div>
            <span className="text-xl font-bold text-dark">{kpis.attendance_rate || 0}%</span>
            <span className="text-[9px] text-emerald-600 font-medium block mt-0.5">Punctuality Score</span>
          </div>
        </div>
      </div>

      {/* Main Charts & Analytics Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Attendance Trends Area Chart */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card lg:col-span-2">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-border">
            <div>
              <h2 className="text-xs font-bold text-dark">Attendance & Late Trends</h2>
              <p className="text-[11px] text-secondary mt-0.5">Workforce Attendance Trends (7-Day Overview) &bull; Headcount & punctuality volume</p>
            </div>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-secondary">
              Active Scope
            </span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="presentGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10B981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="lateGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748B' }} stroke="#CBD5E1" />
                <YAxis tick={{ fontSize: 10, fill: '#64748B' }} stroke="#CBD5E1" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    fontSize: '11px',
                  }}
                />
                <Area type="monotone" dataKey="present" name="Present" stroke="#10B981" fill="url(#presentGrad)" strokeWidth={2} />
                <Area type="monotone" dataKey="late" name="Late Arrivals" stroke="#F59E0B" fill="url(#lateGrad)" strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Department Performance or Shift Overview */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <h2 className="text-xs font-bold text-dark">
              {isAdmin ? 'Department Rates & Performance' : 'Department Rates & Statistics'}
            </h2>
            <Link to="/attendance" className="text-[11px] text-primary hover:underline font-medium">
              Details &rarr;
            </Link>
          </div>
          <div className="space-y-3">
            {deptStats.slice(0, 5).map((d: any, idx: number) => (
              <div key={idx} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-dark">{d.department}</span>
                  <span className="text-secondary font-mono">{d.rate}%</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      d.rate >= 90 ? 'bg-emerald-500' : d.rate >= 80 ? 'bg-amber-500' : 'bg-rose-500'
                    }`}
                    style={{ width: `${d.rate}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] text-secondary">
                  <span>{d.present} present</span>
                  <span>{d.absent} absent</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Second Analytics Row: Overtime Distribution & Leave Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overtime Distribution */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-3 pb-3 border-b border-border">
            <h2 className="text-xs font-bold text-dark">Overtime Distribution by Department</h2>
            <span className="text-[10px] text-secondary">Accumulated Hours</span>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={overtimeDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="department" tick={{ fontSize: 9, fill: '#64748B' }} stroke="#CBD5E1" />
                <YAxis tick={{ fontSize: 10, fill: '#64748B' }} stroke="#CBD5E1" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderRadius: '8px',
                    border: '1px solid #E2E8F0',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="overtime_hours" name="Overtime (hrs)" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Leave Distribution & Shift Overview */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <h2 className="text-xs font-bold text-dark">Workforce Leave Distribution (Active Year)</h2>
            <Link to="/leave" className="text-[11px] text-primary hover:underline font-medium">
              Manage Leave &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {leaveDist.map((item: any, idx: number) => (
              <div key={idx} className="p-3 bg-slate-50 border border-border rounded-lg text-center">
                <span className="text-[10px] font-semibold text-secondary uppercase block">{item.type}</span>
                <span className="text-lg font-bold text-dark block mt-0.5">{item.days}d</span>
                <span className="text-[10px] text-secondary block">{item.count} approved</span>
              </div>
            ))}
          </div>

          {/* Active Shift Coverage Snapshot */}
          <div className="pt-2 border-t border-border">
            <span className="text-[10px] font-bold text-secondary uppercase tracking-wider block mb-2">
              Operational Shifts
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              {shiftOverview.slice(0, 3).map((s: any) => (
                <div key={s.id} className="p-2 rounded bg-slate-50 border border-border">
                  <p className="font-semibold text-dark truncate">{s.name}</p>
                  <p className="text-[10px] text-secondary">{s.start_time} - {s.end_time}</p>
                  <span className="text-[9px] text-primary font-medium">{s.assigned_employees} staff assigned</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Third Row: Needs Attention & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Needs Attention Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-warning" />
              <h2 className="text-xs font-bold text-dark">Needs Attention / Pending Anomalies</h2>
            </div>
            <Link to="/anomalies" className="text-[11px] text-primary hover:underline font-medium">
              Review all &rarr;
            </Link>
          </div>
          <div className="space-y-2">
            {needsAttention.length === 0 ? (
              <div className="py-6 text-center text-secondary text-xs">
                <CheckCircle2 className="w-6 h-6 text-emerald-500 mx-auto mb-1.5" />
                <span>Zero pending anomalies. All shifts operating normally.</span>
              </div>
            ) : (
              needsAttention.map((item: any) => (
                <div
                  key={item.id}
                  className="p-3 bg-slate-50 border border-border rounded-lg flex items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-dark">{item.employee}</span>
                      <span
                        className={`px-1.5 py-0.2 rounded text-[9px] font-bold uppercase ${
                          item.severity === 'high'
                            ? 'bg-red-100 text-danger'
                            : item.severity === 'medium'
                            ? 'bg-amber-100 text-warning'
                            : 'bg-blue-100 text-primary'
                        }`}
                      >
                        {item.severity}
                      </span>
                    </div>
                    <p className="text-[11px] text-secondary mt-0.5">{item.explanation}</p>
                    <span className="text-[9px] text-slate-400">{item.date}</span>
                  </div>
                  <Link
                    to="/anomalies"
                    className="px-2.5 py-1 bg-white border border-border rounded text-[11px] font-semibold text-primary hover:bg-slate-100 flex-shrink-0"
                  >
                    Investigate
                  </Link>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Activity Table */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-border">
            <h2 className="text-xs font-bold text-dark">Recent Workforce Activity</h2>
            <Link to="/attendance" className="text-[11px] text-primary hover:underline font-medium">
              Full Attendance Sheet &rarr;
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border text-secondary text-[11px]">
                  <th className="pb-2 font-semibold">Employee</th>
                  <th className="pb-2 font-semibold">Department</th>
                  <th className="pb-2 font-semibold">Clock In</th>
                  <th className="pb-2 font-semibold">Worked</th>
                  <th className="pb-2 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {recentActivity.slice(0, 6).map((item: any) => (
                  <tr key={item.id} className="hover:bg-slate-50/50">
                    <td className="py-2 font-medium text-dark">{item.employee}</td>
                    <td className="py-2 text-secondary">{item.department}</td>
                    <td className="py-2 text-secondary">{item.clock_in}</td>
                    <td className="py-2 font-semibold text-dark">{item.worked_hours}h</td>
                    <td className="py-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize ${
                          item.status === 'present'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : item.status === 'late'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Fourth Row: AI Workforce Insights Cards */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-border">
          <Sparkles className="w-4 h-4 text-primary" />
          <h2 className="text-xs font-bold text-dark">
            {isAdmin ? 'AI Workforce Intelligence Insights' : 'AI HR Operational Insights'}
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {aiInsights.map((insight: any, idx: number) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border text-xs space-y-1 ${
                insight.level === 'warning'
                  ? 'bg-amber-50/50 border-amber-200 text-amber-900'
                  : insight.level === 'positive'
                  ? 'bg-emerald-50/50 border-emerald-200 text-emerald-900'
                  : 'bg-blue-50/50 border-blue-200 text-blue-900'
              }`}
            >
              <span className="font-bold block text-dark">{insight.title}</span>
              <p className="text-[11px] text-secondary leading-snug">{insight.insight}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
