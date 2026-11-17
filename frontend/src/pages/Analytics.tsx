import React, { useEffect, useState } from 'react';
import { Download, FileSpreadsheet, BarChart2, TrendingUp, Users, Clock, AlertTriangle } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
} from 'recharts';
import { api } from '../services/api';
import { DashboardData } from '../types';

export const Analytics: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const res = await api.get('/analytics/dashboard');
        setData(res.data);
      } catch (e) {
        console.error('Failed to load analytics:', e);
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Analytics & Workforce Reports</h1>
          <p className="text-xs text-secondary mt-0.5">
            Cross-department comparisons, punctuality distributions and compliance exports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="/api/v1/exports/attendance/csv"
            download
            className="px-3.5 py-1.5 bg-white border border-border text-dark hover:bg-slate-50 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-secondary" />
            <span>Download CSV</span>
          </a>
          <a
            href="/api/v1/exports/attendance/xlsx"
            download
            className="px-3.5 py-1.5 bg-primary text-white hover:bg-primary-hover rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Download XLSX</span>
          </a>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Rate Trend */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card">
          <h2 className="text-sm font-bold text-dark mb-1">Attendance Rate Dynamics (%)</h2>
          <p className="text-xs text-secondary mb-4">Past 7 days organization-wide percentage trend</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.trends || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <YAxis domain={[70, 100]} tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: any) => [`${val}%`, 'Attendance Rate']}
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Line type="monotone" dataKey="rate" stroke="#16A34A" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Department Present vs Absent Headcount */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-card">
          <h2 className="text-sm font-bold text-dark mb-1">Department Headcount Distribution</h2>
          <p className="text-xs text-secondary mb-4">Present vs Absent headcount by department</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.department_stats || []}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="department" tick={{ fontSize: 10, fill: '#111827' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#64748B' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                    fontSize: '11px',
                  }}
                />
                <Bar dataKey="present" fill="#2563EB" name="Present" radius={[4, 4, 0, 0]} />
                <Bar dataKey="absent" fill="#EF4444" name="Absent" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Summary KPI Details */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-card">
        <h2 className="text-sm font-bold text-dark mb-4">Workforce Reliability Summary</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-lg bg-slate-50 border border-border">
            <span className="text-secondary block font-medium">Organization Attendance Ratio</span>
            <span className="text-xl font-bold text-dark mt-1 block">{data?.kpis.attendance_rate}%</span>
            <span className="text-[10px] text-success mt-1 block">Healthy enterprise baseline (&gt;90%)</span>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-border">
            <span className="text-secondary block font-medium">Overtime Load Today</span>
            <span className="text-xl font-bold text-dark mt-1 block">{data?.kpis.overtime_hours} Hours</span>
            <span className="text-[10px] text-secondary mt-1 block">Distributed across production shifts</span>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-border">
            <span className="text-secondary block font-medium">Punctuality Deviation</span>
            <span className="text-xl font-bold text-dark mt-1 block">{data?.kpis.late_arrivals} Late Arrivals</span>
            <span className="text-[10px] text-warning mt-1 block">Subject to 15-minute grace window</span>
          </div>
        </div>
      </div>
    </div>
  );
};
