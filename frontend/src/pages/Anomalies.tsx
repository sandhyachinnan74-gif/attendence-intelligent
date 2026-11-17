import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Play,
  CheckCircle2,
  XCircle,
  Filter,
  Info,
  ShieldAlert,
  BrainCircuit,
  Search,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import { AttendanceAnomaly } from '../types';

export const Anomalies: React.FC = () => {
  const [anomalies, setAnomalies] = useState<AttendanceAnomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);

  // Filters
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Review modal
  const [reviewingAnomaly, setReviewingAnomaly] = useState<AttendanceAnomaly | null>(null);
  const [resolutionStatus, setResolutionStatus] = useState<'resolved' | 'dismissed'>('resolved');
  const [resolutionNotes, setResolutionNotes] = useState('');

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (severityFilter) params.severity = severityFilter;
      if (statusFilter) params.status_filter = statusFilter;
      const res = await api.get('/anomalies', { params });
      setAnomalies(res.data);
    } catch (e) {
      console.error('Failed to load anomalies:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, [severityFilter, statusFilter]);

  const handleRunDetection = async () => {
    setDetecting(true);
    try {
      const res = await api.post('/anomalies/detect');
      alert(res.data.message);
      fetchAnomalies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to execute anomaly detection pipeline');
    } finally {
      setDetecting(false);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewingAnomaly) return;
    try {
      await api.put(`/anomalies/${reviewingAnomaly.id}/review`, {
        status: resolutionStatus,
        resolution_notes: resolutionNotes,
      });
      setReviewingAnomaly(null);
      setResolutionNotes('');
      fetchAnomalies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to submit review');
    }
  };

  const totalCount = anomalies.length;
  const criticalCount = anomalies.filter((a) => a.severity === 'critical').length;
  const pendingCount = anomalies.filter((a) => a.status === 'pending').length;
  const resolvedCount = anomalies.filter((a) => a.status === 'resolved').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Workforce Anomaly Detection</h1>
          <p className="text-xs text-secondary mt-0.5">
            Hybrid intelligence engine combining deterministic rules and scikit-learn Isolation Forest.
          </p>
        </div>
        <button
          onClick={handleRunDetection}
          disabled={detecting}
          className="px-3.5 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors disabled:opacity-50"
        >
          {detecting ? (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <Play className="w-3.5 h-3.5 fill-white" />
          )}
          <span>Run Detection Pipeline</span>
        </button>
      </div>

      {/* Ethics & Fairness Notice */}
      <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200/80 text-blue-900 text-xs flex items-start gap-2.5">
        <Info className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Fairness & Compliance Notice:</span>
          <span className="text-blue-800 ml-1">
            Anomalies flagged by AttendAI are statistical investigation indicators, never automated disciplinary actions
            or definitive evidence of misconduct.
          </span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
            Total Anomalies
          </span>
          <span className="text-2xl font-bold text-dark">{totalCount}</span>
          <span className="text-[10px] text-secondary block mt-1">Past 30-day window</span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-danger uppercase tracking-wider block mb-1">
            Critical Alerts
          </span>
          <span className="text-2xl font-bold text-danger">{criticalCount}</span>
          <span className="text-[10px] text-danger/80 block mt-1">Requires supervisor check</span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-warning uppercase tracking-wider block mb-1">
            Pending Review
          </span>
          <span className="text-2xl font-bold text-warning">{pendingCount}</span>
          <span className="text-[10px] text-warning/80 block mt-1">Open triage queue</span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-success uppercase tracking-wider block mb-1">
            Resolved / Audited
          </span>
          <span className="text-2xl font-bold text-success">{resolvedCount}</span>
          <span className="text-[10px] text-success/80 block mt-1">With resolution notes</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-wrap items-center gap-3 justify-between">
        <div className="flex items-center gap-3">
          <Filter className="w-3.5 h-3.5 text-secondary" />
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="py-1 px-3 bg-slate-50 border border-border rounded-lg text-xs text-dark"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="py-1 px-3 bg-slate-50 border border-border rounded-lg text-xs text-dark"
          >
            <option value="">All Review Statuses</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </div>
      </div>

      {/* Anomalies Table */}
      <div className="bg-card border border-border rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Employee</th>
                <th className="py-3 px-4">Anomaly Type</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Method</th>
                <th className="py-3 px-4">Score</th>
                <th className="py-3 px-4">Explanation</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-medium">
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center py-10 text-secondary">
                    Loading anomaly queue...
                  </td>
                </tr>
              ) : anomalies.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-10 text-secondary">
                    No anomalies found matching current filters.
                  </td>
                </tr>
              ) : (
                anomalies.map((anom) => (
                  <tr key={anom.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4 font-mono text-dark">{anom.date}</td>
                    <td className="py-3 px-4">
                      <span className="font-semibold text-dark block">{anom.employee_name}</span>
                      <span className="text-[10px] text-secondary font-mono">{anom.employee_code}</span>
                    </td>
                    <td className="py-3 px-4 font-semibold text-dark capitalize">
                      {anom.anomaly_type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                          anom.severity === 'critical'
                            ? 'bg-rose-50 text-danger border-rose-200'
                            : anom.severity === 'high'
                            ? 'bg-amber-50 text-warning border-amber-200'
                            : 'bg-blue-50 text-primary border-blue-200'
                        }`}
                      >
                        {anom.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="flex items-center gap-1 text-[11px] text-secondary capitalize">
                        {anom.detection_method === 'isolation_forest' ? (
                          <>
                            <BrainCircuit className="w-3.5 h-3.5 text-purple-600" />
                            <span>Isolation Forest</span>
                          </>
                        ) : (
                          <>
                            <ShieldAlert className="w-3.5 h-3.5 text-blue-600" />
                            <span>Rule-Based</span>
                          </>
                        )}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-dark">{anom.score}</td>
                    <td className="py-3 px-4 text-secondary max-w-sm truncate" title={anom.explanation}>
                      {anom.explanation}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold capitalize border ${
                          anom.status === 'resolved'
                            ? 'bg-emerald-50 text-success border-emerald-200'
                            : anom.status === 'dismissed'
                            ? 'bg-slate-100 text-secondary border-slate-200'
                            : 'bg-amber-50 text-warning border-amber-200'
                        }`}
                      >
                        {anom.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {anom.status === 'pending' && (
                        <button
                          onClick={() => {
                            setReviewingAnomaly(anom);
                            setResolutionNotes('');
                          }}
                          className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 border border-border text-[11px] font-medium text-dark rounded-md"
                        >
                          Triage
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Review Modal */}
      {reviewingAnomaly && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Investigate Anomaly Flag</h3>
              <button onClick={() => setReviewingAnomaly(null)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleReviewSubmit} className="p-6 space-y-4">
              <div className="p-3 bg-slate-50 border border-border rounded-lg space-y-1 text-xs">
                <p className="font-bold text-dark">{reviewingAnomaly.employee_name}</p>
                <p className="text-secondary">
                  Flagged: {reviewingAnomaly.anomaly_type.replace(/_/g, ' ')} &bull; {reviewingAnomaly.date}
                </p>
                <p className="text-dark font-medium mt-1">{reviewingAnomaly.explanation}</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Resolution Action</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-1.5 text-xs text-dark cursor-pointer">
                    <input
                      type="radio"
                      name="resolution_status"
                      value="resolved"
                      checked={resolutionStatus === 'resolved'}
                      onChange={() => setResolutionStatus('resolved')}
                      className="text-primary focus:ring-primary"
                    />
                    <span>Resolve (Confirm Valid Investigation)</span>
                  </label>
                  <label className="flex items-center gap-1.5 text-xs text-dark cursor-pointer">
                    <input
                      type="radio"
                      name="resolution_status"
                      value="dismissed"
                      checked={resolutionStatus === 'dismissed'}
                      onChange={() => setResolutionStatus('dismissed')}
                      className="text-primary focus:ring-primary"
                    />
                    <span>Dismiss (False Positive)</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Resolution Notes</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Record outcome of supervisor consultation..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setReviewingAnomaly(null)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm"
                >
                  Save Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
