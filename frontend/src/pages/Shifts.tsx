import React, { useEffect, useState } from 'react';
import { Plus, Calendar, Clock, Moon, Sun, CheckCircle, Users, X } from 'lucide-react';
import { api } from '../services/api';
import { Shift, Employee } from '../types';

export const Shifts: React.FC = () => {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);

  const [newShift, setNewShift] = useState({
    name: '',
    code: '',
    start_time: '09:00',
    end_time: '17:30',
    grace_period_minutes: 15,
    required_hours: 8.0,
    is_overnight: false,
  });

  const [assignment, setAssignment] = useState({
    employee_id: '',
    shift_id: '',
    effective_from: new Date().toISOString().split('T')[0],
  });

  const fetchShifts = async () => {
    setLoading(true);
    try {
      const res = await api.get('/shifts');
      setShifts(res.data);
    } catch (e) {
      console.error('Failed to load shifts:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployees = async () => {
    try {
      const res = await api.get('/employees');
      setEmployees(res.data);
    } catch (e) {
      console.error('Failed to load employees:', e);
    }
  };

  useEffect(() => {
    fetchShifts();
    fetchEmployees();
  }, []);

  const handleCreateShift = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/shifts', newShift);
      setShowCreateModal(false);
      setNewShift({
        name: '',
        code: '',
        start_time: '09:00',
        end_time: '17:30',
        grace_period_minutes: 15,
        required_hours: 8.0,
        is_overnight: false,
      });
      fetchShifts();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create shift');
    }
  };

  const handleAssignShift = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/shifts/assign', assignment);
      setShowAssignModal(false);
      alert('Shift assigned successfully!');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to assign shift');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Shifts & Scheduling</h1>
          <p className="text-xs text-secondary mt-0.5">Manage working shift definitions, grace periods and assignments.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAssignModal(true)}
            className="px-3.5 py-1.5 bg-white border border-border text-dark rounded-lg text-xs font-semibold hover:bg-slate-50 flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Users className="w-4 h-4 text-secondary" />
            <span>Assign Shift</span>
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-3.5 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Create Shift</span>
          </button>
        </div>
      </div>

      {/* Shift Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {shifts.map((s) => (
          <div key={s.id} className="bg-card border border-border rounded-xl p-5 shadow-card flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="px-2 py-0.5 bg-slate-100 text-secondary text-[10px] font-mono font-bold rounded-md uppercase">
                  {s.code}
                </span>
                {s.is_overnight ? (
                  <span className="flex items-center gap-1 text-[10px] text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded-full font-semibold">
                    <Moon className="w-3 h-3" />
                    Overnight
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[10px] text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full font-semibold">
                    <Sun className="w-3 h-3" />
                    Day Shift
                  </span>
                )}
              </div>
              <h3 className="text-base font-bold text-dark">{s.name}</h3>
              <p className="text-lg font-mono font-bold text-primary mt-2">
                {s.start_time.substring(0, 5)} &ndash; {s.end_time.substring(0, 5)}
              </p>
            </div>

            <div className="mt-5 pt-3 border-t border-border/80 text-xs text-secondary space-y-1">
              <div className="flex justify-between">
                <span>Grace Window:</span>
                <span className="font-semibold text-dark">{s.grace_period_minutes} mins</span>
              </div>
              <div className="flex justify-between">
                <span>Required Duration:</span>
                <span className="font-semibold text-dark">{s.required_hours} hours</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Shift Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Define New Shift</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateShift} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark mb-1">Shift Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Afternoon Support Shift"
                  value={newShift.name}
                  onChange={(e) => setNewShift({ ...newShift, name: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Shift Code</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. AFT"
                  value={newShift.code}
                  onChange={(e) => setNewShift({ ...newShift, code: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Start Time</label>
                  <input
                    type="time"
                    required
                    value={newShift.start_time}
                    onChange={(e) => setNewShift({ ...newShift, start_time: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">End Time</label>
                  <input
                    type="time"
                    required
                    value={newShift.end_time}
                    onChange={(e) => setNewShift({ ...newShift, end_time: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Grace Period (mins)</label>
                  <input
                    type="number"
                    required
                    min={0}
                    max={60}
                    value={newShift.grace_period_minutes}
                    onChange={(e) => setNewShift({ ...newShift, grace_period_minutes: parseInt(e.target.value) })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Required Hours</label>
                  <input
                    type="number"
                    step="0.5"
                    required
                    min={1}
                    max={24}
                    value={newShift.required_hours}
                    onChange={(e) => setNewShift({ ...newShift, required_hours: parseFloat(e.target.value) })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="is_overnight"
                  checked={newShift.is_overnight}
                  onChange={(e) => setNewShift({ ...newShift, is_overnight: e.target.checked })}
                  className="rounded text-primary focus:ring-primary"
                />
                <label htmlFor="is_overnight" className="text-xs text-dark font-medium cursor-pointer">
                  Crosses midnight (Overnight shift)
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm"
                >
                  Save Shift
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Shift Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Assign Shift to Employee</h3>
              <button onClick={() => setShowAssignModal(false)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAssignShift} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark mb-1">Select Employee</label>
                <select
                  required
                  value={assignment.employee_id}
                  onChange={(e) => setAssignment({ ...assignment, employee_id: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                >
                  <option value="">Select Employee</option>
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.first_name} {emp.last_name} ({emp.employee_code})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Select Shift</label>
                <select
                  required
                  value={assignment.shift_id}
                  onChange={(e) => setAssignment({ ...assignment, shift_id: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                >
                  <option value="">Select Shift</option>
                  {shifts.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.start_time.substring(0, 5)} - {s.end_time.substring(0, 5)})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Effective Date</label>
                <input
                  type="date"
                  required
                  value={assignment.effective_from}
                  onChange={(e) => setAssignment({ ...assignment, effective_from: e.target.value })}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowAssignModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm"
                >
                  Assign Shift
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
