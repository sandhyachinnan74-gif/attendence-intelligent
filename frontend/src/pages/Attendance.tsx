import React, { useEffect, useState } from 'react';
import {
  Clock,
  Play,
  Square,
  Coffee,
  Calendar,
  Download,
  Filter,
  CheckCircle2,
  AlertCircle,
  FileSpreadsheet,
  Edit,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import { AttendanceRecord } from '../types';
import { useAuth } from '../context/AuthContext';

export const Attendance: React.FC = () => {
  const { user } = useAuth();
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  // Filters
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Live Clock
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());

  // Correction Modal
  const [correctingRecord, setCorrectingRecord] = useState<AttendanceRecord | null>(null);
  const [correctionData, setCorrectionData] = useState({
    clock_in: '',
    clock_out: '',
    reason: '',
  });

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchTodayStatus = async () => {
    try {
      const res = await api.get('/attendance/today');
      setTodayRecord(res.data);
    } catch (e) {
      console.error('Failed to load today record:', e);
    }
  };

  const fetchRecords = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (statusFilter) params.status_filter = statusFilter;
      const res = await api.get('/attendance', { params });
      setRecords(res.data);
    } catch (e) {
      console.error('Failed to load attendance list:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTodayStatus();
    fetchRecords();
  }, [startDate, endDate, statusFilter]);

  const handleClockIn = async () => {
    setActionLoading(true);
    try {
      await api.post('/attendance/clock-in', {});
      await fetchTodayStatus();
      await fetchRecords();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to clock in');
    } finally {
      setActionLoading(false);
    }
  };

  const handleClockOut = async () => {
    setActionLoading(true);
    try {
      await api.post('/attendance/clock-out', {});
      await fetchTodayStatus();
      await fetchRecords();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to clock out');
    } finally {
      setActionLoading(false);
    }
  };

  const handleToggleBreak = async () => {
    setActionLoading(true);
    try {
      await api.post('/attendance/break', { reason: 'Break' });
      await fetchTodayStatus();
      await fetchRecords();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to toggle break');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCorrectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!correctingRecord) return;
    try {
      await api.post(`/attendance/${correctingRecord.id}/correct`, {
        clock_in: correctionData.clock_in ? new Date(correctionData.clock_in).toISOString() : null,
        clock_out: correctionData.clock_out ? new Date(correctionData.clock_out).toISOString() : null,
        reason: correctionData.reason,
      });
      setCorrectingRecord(null);
      fetchRecords();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit correction');
    }
  };

  const isClockedIn = !!todayRecord?.clock_in && !todayRecord?.clock_out;
  const isClockedOut = !!todayRecord?.clock_in && !!todayRecord?.clock_out;
  const hasOpenBreak = todayRecord?.breaks?.some((b) => !b.break_end);

  const canCorrect = user?.role === 'admin' || user?.role === 'hr_manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Time & Attendance</h1>
          <p className="text-xs text-secondary mt-0.5">Punch tracking, worked hours, breaks and audit records.</p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="/api/v1/exports/attendance/csv"
            download
            className="px-3 py-1.5 bg-white border border-border text-dark hover:bg-slate-50 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-secondary" />
            <span>CSV Export</span>
          </a>
          <a
            href="/api/v1/exports/attendance/xlsx"
            download
            className="px-3 py-1.5 bg-white border border-border text-dark hover:bg-slate-50 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow-sm"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>XLSX Export</span>
          </a>
        </div>
      </div>

      {/* Live Punch Action Card */}
      <div className="bg-card border border-border rounded-xl p-6 shadow-card flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
            <Clock className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold font-mono tracking-tight text-dark">{currentTime}</span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                  hasOpenBreak
                    ? 'bg-amber-50 text-warning border-amber-200'
                    : isClockedIn
                    ? 'bg-emerald-50 text-success border-emerald-200'
                    : isClockedOut
                    ? 'bg-slate-100 text-secondary border-slate-200'
                    : 'bg-blue-50 text-primary border-blue-200'
                }`}
              >
                {hasOpenBreak ? 'On Break' : isClockedIn ? 'Clocked In' : isClockedOut ? 'Clocked Out' : 'Ready'}
              </span>
            </div>
            <p className="text-xs text-secondary mt-1">
              {todayRecord?.clock_in
                ? `Clocked in at ${new Date(todayRecord.clock_in).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}`
                : 'No punch recorded yet today.'}
              {todayRecord?.clock_out &&
                ` • Clocked out at ${new Date(todayRecord.clock_out).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}`}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          {!isClockedIn && !isClockedOut && (
            <button
              onClick={handleClockIn}
              disabled={actionLoading}
              className="flex-1 md:flex-none px-5 py-2.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center justify-center gap-2 shadow-sm transition-colors disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-white" />
              <span>Clock In</span>
            </button>
          )}

          {isClockedIn && (
            <>
              <button
                onClick={handleToggleBreak}
                disabled={actionLoading}
                className="flex-1 md:flex-none px-4 py-2.5 bg-amber-500 text-white rounded-lg text-xs font-semibold hover:bg-amber-600 flex items-center justify-center gap-2 shadow-sm transition-colors disabled:opacity-50"
              >
                <Coffee className="w-4 h-4" />
                <span>{hasOpenBreak ? 'End Break' : 'Start Break'}</span>
              </button>
              <button
                onClick={handleClockOut}
                disabled={actionLoading}
                className="flex-1 md:flex-none px-5 py-2.5 bg-danger text-white rounded-lg text-xs font-semibold hover:bg-red-600 flex items-center justify-center gap-2 shadow-sm transition-colors disabled:opacity-50"
              >
                <Square className="w-4 h-4 fill-white" />
                <span>Clock Out</span>
              </button>
            </>
          )}

          {isClockedOut && (
            <div className="px-4 py-2 rounded-lg bg-slate-50 border border-border text-xs text-secondary font-medium">
              Daily shift completed ({Math.round((todayRecord.worked_minutes / 60) * 10) / 10} hours worked).
            </div>
          )}
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-wrap items-center gap-3 justify-between">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-secondary">
            <span>From:</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="py-1 px-2.5 bg-slate-50 border border-border rounded-lg text-xs text-dark"
            />
          </div>
          <div className="flex items-center gap-1.5 text-xs text-secondary">
            <span>To:</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="py-1 px-2.5 bg-slate-50 border border-border rounded-lg text-xs text-dark"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="py-1 px-3 bg-slate-50 border border-border rounded-lg text-xs text-dark"
          >
            <option value="">All Statuses</option>
            <option value="present">Present</option>
            <option value="late">Late</option>
            <option value="half_day">Half Day</option>
            <option value="incomplete">Incomplete</option>
          </select>
        </div>
      </div>

      {/* Attendance History Table */}
      <div className="bg-card border border-border rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Employee</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Clock In</th>
                <th className="py-3 px-4">Clock Out</th>
                <th className="py-3 px-4">Worked</th>
                <th className="py-3 px-4">Overtime</th>
                <th className="py-3 px-4">Late</th>
                <th className="py-3 px-4">Status</th>
                {canCorrect && <th className="py-3 px-4 text-right">Action</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-medium">
              {loading ? (
                <tr>
                  <td colSpan={10} className="text-center py-10 text-secondary">
                    Loading records...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={10} className="text-center py-10 text-secondary">
                    No attendance records found for the selected criteria.
                  </td>
                </tr>
              ) : (
                records.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4 font-mono text-dark">{r.date}</td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-dark block">{r.employee_name}</span>
                      <span className="text-[10px] text-secondary font-mono">{r.employee_code}</span>
                    </td>
                    <td className="py-3 px-4 text-secondary">{r.department_name}</td>
                    <td className="py-3 px-4 font-mono text-dark">
                      {r.clock_in ? new Date(r.clock_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
                    </td>
                    <td className="py-3 px-4 font-mono text-dark">
                      {r.clock_out ? new Date(r.clock_out).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '-'}
                    </td>
                    <td className="py-3 px-4 font-mono text-dark">{Math.round((r.worked_minutes / 60) * 10) / 10}h</td>
                    <td className="py-3 px-4 font-mono text-indigo-600">
                      {r.overtime_minutes > 0 ? `${Math.round((r.overtime_minutes / 60) * 10) / 10}h` : '-'}
                    </td>
                    <td className="py-3 px-4 font-mono text-warning">{r.late_minutes > 0 ? `${r.late_minutes}m` : '-'}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                          r.status === 'present'
                            ? 'bg-emerald-50 text-success'
                            : r.status === 'late'
                            ? 'bg-amber-50 text-warning'
                            : r.status === 'half_day'
                            ? 'bg-indigo-50 text-indigo-700'
                            : 'bg-slate-100 text-secondary'
                        }`}
                      >
                        {r.status}
                      </span>
                      {r.is_corrected && (
                        <span className="ml-1 text-[9px] text-primary font-semibold" title="Corrected record">
                          (Audit)
                        </span>
                      )}
                    </td>
                    {canCorrect && (
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => {
                            setCorrectingRecord(r);
                            setCorrectionData({
                              clock_in: r.clock_in ? r.clock_in.substring(0, 16) : '',
                              clock_out: r.clock_out ? r.clock_out.substring(0, 16) : '',
                              reason: '',
                            });
                          }}
                          className="p-1 rounded text-secondary hover:text-primary transition-colors"
                          title="Correct Attendance Record"
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Attendance Correction Modal */}
      {correctingRecord && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Audit Attendance Correction</h3>
              <button onClick={() => setCorrectingRecord(null)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCorrectionSubmit} className="p-6 space-y-4">
              <div className="p-3 bg-slate-50 border border-border rounded-lg text-xs space-y-1">
                <p className="font-semibold text-dark">{correctingRecord.employee_name}</p>
                <p className="text-secondary">Date: {correctingRecord.date}</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Clock In Time</label>
                <input
                  type="datetime-local"
                  value={correctionData.clock_in}
                  onChange={(e) => setCorrectionData({ ...correctionData, clock_in: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Clock Out Time</label>
                <input
                  type="datetime-local"
                  value={correctionData.clock_out}
                  onChange={(e) => setCorrectionData({ ...correctionData, clock_out: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Audit Reason (Required)</label>
                <textarea
                  required
                  rows={2}
                  placeholder="e.g. Employee forgot to clock out due to offsite client emergency"
                  value={correctionData.reason}
                  onChange={(e) => setCorrectionData({ ...correctionData, reason: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setCorrectingRecord(null)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm"
                >
                  Commit Correction
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
