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
import { DashboardData } from '../types';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = async () => {
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
    fetchDashboard();
  }, []);

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

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
            onClick={fetchDashboard}
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
              <span>Past grace window</span>
            </div>
          </div>
        </div>

        {/* Overtime Hours */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Overtime</span>
            <div className="w-7 h-7 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.overtime_hours || 0}h</span>
            <div className="flex items-center gap-1 text-[11px] text-secondary mt-1 font-medium">
              <span>Cumulative today</span>
            </div>
          </div>
        </div>

        {/* Attendance Rate */}
        <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col justify-between">
          <div className="flex items-center justify-between text-secondary mb-2">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Rate</span>
            <div className="w-7 h-7 rounded-lg bg-emerald-50 text-success flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold text-dark">{kpis?.attendance_rate || 0}%</span>
            <div className="flex items-center gap-1 text-[11px] text-success mt-1 font-medium">
              <span>Target: &ge;90%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 7-Day Trend Chart */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-5 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-dark">7-Day Attendance Trend</h2>
              <p className="text-[11px] text-secondary">Present vs Absent headcount over past 7 calendar days</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
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
