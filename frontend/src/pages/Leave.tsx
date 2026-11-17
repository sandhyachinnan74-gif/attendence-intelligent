import React, { useEffect, useState } from 'react';
import { Plus, Calendar, Clock, CheckCircle, XCircle, AlertCircle, X, Download, History, FileText, FileSpreadsheet } from 'lucide-react';
import { api } from '../services/api';
import { LeaveRecord } from '../types';
import { useAuth } from '../context/AuthContext';
import { downloadFile } from '../utils/download';

export const Leave: React.FC = () => {
  const { user } = useAuth();
  const [leaves, setLeaves] = useState<LeaveRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingFormat, setDownloadingFormat] = useState<'csv' | 'xlsx' | null>(null);

  const handleDirectExport = async (format: 'csv' | 'xlsx') => {
    setDownloadingFormat(format);
    await downloadFile(
      `/exports/attendance/${format}`,
      `AttendAI_Leave_Attendance.${format}`,
      undefined,
      () => setDownloadingFormat(null),
      (err) => {
        setDownloadingFormat(null);
        window.dispatchEvent(new CustomEvent('attendai:notify', {
          detail: { message: `Export error: ${err}`, type: 'error' }
        }));
      }
    );
  };

  const [showApplyModal, setShowApplyModal] = useState(false);
  const [reviewingLeave, setReviewingLeave] = useState<LeaveRecord | null>(null);

  const [newLeave, setNewLeave] = useState({
    leave_type: 'annual',
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    reason: '',
  });

  const [reviewNotes, setReviewNotes] = useState('');

  const fetchLeaves = async () => {
    setLoading(true);
    try {
      const res = await api.get('/leave');
      setLeaves(res.data);
    } catch (e) {
      console.error('Failed to load leave records:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaves();
  }, []);

  const handleApplyLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/leave', newLeave);
      setShowApplyModal(false);
      setNewLeave({
        leave_type: 'annual',
        start_date: new Date().toISOString().split('T')[0],
        end_date: new Date().toISOString().split('T')[0],
        reason: '',
      });
      fetchLeaves();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to apply for leave');
    }
  };

  const handleReview = async (status: 'approved' | 'rejected') => {
    if (!reviewingLeave) return;
    try {
      await api.put(`/leave/${reviewingLeave.id}/review`, {
        status,
        resolution_notes: reviewNotes,
      });
      setReviewingLeave(null);
      setReviewNotes('');
      fetchLeaves();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to review leave application');
    }
  };

  const canReview = user?.role === 'admin' || user?.role === 'hr_manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Leave Management</h1>
          <p className="text-xs text-secondary mt-0.5">Apply for paid time off, track requests and manage approvals.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleDirectExport('csv')}
            disabled={downloadingFormat !== null}
            className="px-3 py-1.5 bg-white border border-border text-dark hover:bg-slate-50 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer disabled:opacity-50"
            title="Download Leave / Attendance CSV"
          >
            <FileText className="w-3.5 h-3.5 text-blue-600" />
            <span>{downloadingFormat === 'csv' ? 'Exporting...' : 'Export CSV'}</span>
          </button>
          <button
            onClick={() => handleDirectExport('xlsx')}
            disabled={downloadingFormat !== null}
            className="px-3 py-1.5 bg-primary text-white hover:bg-primary-hover rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer disabled:opacity-50"
            title="Download Day-Wise Attendance Excel Report"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>{downloadingFormat === 'xlsx' ? 'Exporting...' : 'Export XLS'}</span>
          </button>
          <button
            onClick={() => setShowApplyModal(true)}
            className="px-3.5 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Apply for Leave</span>
          </button>
        </div>
      </div>

      {/* Leave Balance Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
            Annual Leave
          </span>
          <span className="text-2xl font-bold text-dark">20 Days</span>
          <span className="text-[10px] text-secondary block mt-1">Paid allowance / year</span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
            Sick Leave
          </span>
          <span className="text-2xl font-bold text-dark">10 Days</span>
          <span className="text-[10px] text-secondary block mt-1">Medical certificate &gt;3d</span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
            Casual Leave
          </span>
          <span className="text-2xl font-bold text-dark">5 Days</span>
          <span className="text-[10px] text-secondary block mt-1">Personal emergencies</span>
        </div>
        <div className="bg-card border border-border rounded-xl p-4 shadow-card">
          <span className="text-[11px] font-semibold text-secondary uppercase tracking-wider block mb-1">
            Unpaid Leave
          </span>
          <span className="text-2xl font-bold text-dark">Discretionary</span>
          <span className="text-[10px] text-secondary block mt-1">Subject to HR approval</span>
        </div>
      </div>

      {/* Leave Applications Table */}
      <div className="bg-card border border-border rounded-xl shadow-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Employee</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Start Date</th>
                <th className="py-3 px-4">End Date</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Reason</th>
                <th className="py-3 px-4">Status</th>
                {canReview && <th className="py-3 px-4 text-right">Review</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-medium">
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-secondary">
                    Loading requests...
                  </td>
                </tr>
              ) : leaves.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-10 text-secondary">
                    No leave applications found.
                  </td>
                </tr>
              ) : (
                leaves.map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <span className="font-semibold text-dark block">{l.employee_name}</span>
                      <span className="text-[10px] text-secondary font-mono">{l.employee_code}</span>
                    </td>
                    <td className="py-3 px-4 capitalize font-semibold text-dark">{l.leave_type}</td>
                    <td className="py-3 px-4 font-mono text-dark">{l.start_date}</td>
                    <td className="py-3 px-4 font-mono text-dark">{l.end_date}</td>
                    <td className="py-3 px-4 font-mono text-dark">{l.days_count} days</td>
                    <td className="py-3 px-4 text-secondary max-w-xs truncate" title={l.reason}>
                      {l.reason}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold capitalize border ${
                          l.status === 'approved'
                            ? 'bg-emerald-50 text-success border-emerald-200'
                            : l.status === 'rejected'
                            ? 'bg-rose-50 text-danger border-rose-200'
                            : 'bg-amber-50 text-warning border-amber-200'
                        }`}
                      >
                        {l.status}
                      </span>
                    </td>
                    {canReview && (
                      <td className="py-3 px-4 text-right">
                        {l.status === 'pending' && (
                          <button
                            onClick={() => {
                              setReviewingLeave(l);
                              setReviewNotes('');
                            }}
                            className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 border border-border text-[11px] font-medium text-dark rounded-md"
                          >
                            Review
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Apply Leave Modal */}
      {showApplyModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Apply for Leave</h3>
              <button onClick={() => setShowApplyModal(false)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleApplyLeave} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark mb-1">Leave Category</label>
                <select
                  value={newLeave.leave_type}
                  onChange={(e) => setNewLeave({ ...newLeave, leave_type: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                >
                  <option value="annual">Annual Leave</option>
                  <option value="sick">Sick Leave</option>
                  <option value="casual">Casual Leave</option>
                  <option value="unpaid">Unpaid Leave</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Start Date</label>
                  <input
                    type="date"
                    required
                    value={newLeave.start_date}
                    onChange={(e) => setNewLeave({ ...newLeave, start_date: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">End Date</label>
                  <input
                    type="date"
                    required
                    value={newLeave.end_date}
                    onChange={(e) => setNewLeave({ ...newLeave, end_date: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Reason for Leave</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Provide context for manager review..."
                  value={newLeave.reason}
                  onChange={(e) => setNewLeave({ ...newLeave, reason: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowApplyModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm"
                >
                  Submit Application
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Review Leave Modal */}
      {reviewingLeave && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Review Leave Application</h3>
              <button onClick={() => setReviewingLeave(null)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div className="p-3 bg-slate-50 border border-border rounded-lg space-y-1">
                <p className="font-bold text-dark text-sm">{reviewingLeave.employee_name}</p>
                <p className="text-secondary">
                  {reviewingLeave.leave_type.toUpperCase()} &bull; {reviewingLeave.days_count} Days ({reviewingLeave.start_date} to {reviewingLeave.end_date})
                </p>
                <p className="text-dark font-medium mt-2">&ldquo;{reviewingLeave.reason}&rdquo;</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Supervisor Resolution Notes</label>
                <textarea
                  rows={2}
                  placeholder="Optional notes or instructions..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => handleReview('rejected')}
                  className="px-4 py-2 bg-rose-50 text-danger border border-rose-200 rounded-lg text-xs font-semibold hover:bg-rose-100"
                >
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => handleReview('approved')}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-xs font-semibold hover:bg-emerald-700 shadow-sm"
                >
                  Approve Application
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
