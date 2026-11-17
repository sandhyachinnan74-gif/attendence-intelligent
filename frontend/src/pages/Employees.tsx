import React, { useEffect, useState } from 'react';
import {
  Plus,
  Search,
  Filter,
  Mail,
  Phone,
  Building2,
  UserCheck,
  UserX,
  Eye,
  X,
  Users,
  ShieldCheck,
  Clock,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Send,
  Download,
  History
} from 'lucide-react';
import { api } from '../services/api';
import { Employee, Department } from '../types';
import { useAuth } from '../context/AuthContext';
import { CustomReportModal } from '../components/reports/CustomReportModal';
import { ExportHistoryModal } from '../components/reports/ExportHistoryModal';

export const Employees: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const isHR = user?.role === 'hr_manager';
  const canManageEmployees = isAdmin || isHR;

  const [activeTab, setActiveTab] = useState<'directory' | 'onboarding'>('directory');
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [loading, setLoading] = useState(true);

  // Onboarding Requests state
  const [onboardingRequests, setOnboardingRequests] = useState<any[]>([]);
  const [onboardingFilter, setOnboardingFilter] = useState<string>('all');
  const [onboardingLoading, setOnboardingLoading] = useState(false);
  const [reviewLoadingId, setReviewLoadingId] = useState<string | null>(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);

  // Reject modal state
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectRequestId, setRejectRequestId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    employee_code: '',
    department_id: '',
    designation: '',
    phone: '',
    date_of_joining: new Date().toISOString().split('T')[0],
    role: 'employee',
  });
  const [submittingOnboard, setSubmittingOnboard] = useState(false);
  const [formMsg, setFormMsg] = useState<{ text: string; error: boolean } | null>(null);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (search) params.search = search;
      if (selectedDept) params.department_id = selectedDept;
      const res = await api.get('/employees', { params });
      setEmployees(res.data);
    } catch (e) {
      console.error('Failed to load employees:', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const res = await api.get('/departments');
      setDepartments(res.data);
    } catch (e) {
      console.error('Failed to load departments:', e);
    }
  };

  const fetchOnboardingRequests = async () => {
    if (!canManageEmployees) return;
    setOnboardingLoading(true);
    try {
      const params: any = {};
      if (onboardingFilter !== 'all') {
        params.status = onboardingFilter;
      }
      const res = await api.get('/employees/onboarding-requests', { params });
      setOnboardingRequests(res.data);
    } catch (e) {
      console.error('Failed to load onboarding requests:', e);
    } finally {
      setOnboardingLoading(false);
    }
  };

  useEffect(() => {
    fetchDepartments();
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [search, selectedDept]);

  useEffect(() => {
    if (canManageEmployees) {
      fetchOnboardingRequests();
    }
  }, [onboardingFilter]);

  const handleCreateEmployeeRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingOnboard(true);
    setFormMsg(null);
    try {
      const res = await api.post('/employees/request', formData);
      const isDirectApproved = res.data?.status === 'approved';
      setFormMsg({
        text: isDirectApproved
          ? 'Employee profile created and authorized successfully!'
          : 'Employee onboarding request submitted! Notification sent to Administrator for authorization.',
        error: false,
      });

      setTimeout(() => {
        setShowAddModal(false);
        setFormMsg(null);
        setFormData({
          first_name: '',
          last_name: '',
          email: '',
          employee_code: '',
          department_id: '',
          designation: '',
          phone: '',
          date_of_joining: new Date().toISOString().split('T')[0],
          role: 'employee',
        });
        fetchEmployees();
        fetchOnboardingRequests();
      }, 1500);
    } catch (err: any) {
      setFormMsg({
        text: err.response?.data?.detail || 'Failed to submit onboarding request',
        error: true,
      });
    } finally {
      setSubmittingOnboard(false);
    }
  };

  const handleReviewRequest = async (requestId: string, status: 'approved' | 'rejected', reason?: string) => {
    setReviewLoadingId(requestId);
    try {
      await api.post(`/employees/onboarding-requests/${requestId}/review`, {
        status,
        rejection_reason: reason || undefined,
      });
      await fetchOnboardingRequests();
      await fetchEmployees();
      if (showRejectModal) {
        setShowRejectModal(false);
        setRejectRequestId(null);
        setRejectionReason('');
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || `Failed to ${status} onboarding request`);
    } finally {
      setReviewLoadingId(null);
    }
  };

  const pendingCount = onboardingRequests.filter((r) => r.status === 'pending_approval').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">
            {isAdmin ? 'Workforce Management & Directory' : 'Employee Directory & Onboarding'}
          </h1>
          <p className="text-xs text-secondary mt-0.5">
            {isAdmin
              ? 'Authorize onboarding requests, manage department mappings and workforce profiles.'
              : 'Submit new employee onboarding requests for Administrator authorization and explore workforce.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowReportModal(true)}
            className="px-3.5 py-1.5 bg-white border border-border text-dark hover:bg-slate-50 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-secondary" />
            <span>Export Employee Data</span>
          </button>
          <button
            onClick={() => setShowHistoryModal(true)}
            className="px-3 py-1.5 bg-white border border-border text-dark hover:bg-slate-50 rounded-lg text-xs font-medium flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
          >
            <History className="w-3.5 h-3.5 text-secondary" />
            <span>History</span>
          </button>
          {canManageEmployees && (
            <button
              onClick={() => {
                setFormMsg(null);
                setShowAddModal(true);
              }}
              className="px-3.5 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>{isAdmin ? 'Add & Authorize Employee' : 'Request New Employee'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabs navigation for HR / Admin */}
      {canManageEmployees && (
        <div className="flex items-center gap-2 border-b border-border pb-1">
          <button
            onClick={() => setActiveTab('directory')}
            className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors flex items-center gap-2 border-b-2 cursor-pointer ${
              activeTab === 'directory'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-secondary hover:text-dark'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Employee Directory ({employees.length})</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('onboarding');
              fetchOnboardingRequests();
            }}
            className={`px-4 py-2 text-xs font-semibold rounded-t-lg transition-colors flex items-center gap-2 border-b-2 cursor-pointer ${
              activeTab === 'onboarding'
                ? 'border-primary text-primary bg-primary/5'
                : 'border-transparent text-secondary hover:text-dark'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Onboarding Approvals</span>
            {pendingCount > 0 && (
              <span className="px-1.5 py-0.2 bg-amber-500 text-white rounded-full text-[10px] font-bold">
                {pendingCount}
              </span>
            )}
          </button>
        </div>
      )}

      {/* TAB 1: EMPLOYEE DIRECTORY */}
      {activeTab === 'directory' && (
        <div className="space-y-4">
          {/* Filter and Search Bar */}
          <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col sm:flex-row items-center gap-3 justify-between">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by name, code, email, designation..."
                className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark placeholder-secondary focus:outline-none focus:ring-1 focus:ring-primary focus:bg-white"
              />
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              <div className="flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-secondary" />
                <select
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value)}
                  className="py-1.5 px-3 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">All Departments</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.code})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Directory Table */}
          <div className="bg-card border border-border rounded-xl shadow-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                    <th className="py-3 px-4">Employee</th>
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Department</th>
                    <th className="py-3 px-4">Designation</th>
                    <th className="py-3 px-4">Joined</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium">
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="text-center py-10 text-secondary">
                        Loading employees...
                      </td>
                    </tr>
                  ) : employees.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-10 text-secondary">
                        No employees matching the search filters.
                      </td>
                    </tr>
                  ) : (
                    employees.map((emp) => (
                      <tr key={emp.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-xs flex-shrink-0">
                              {emp.first_name[0]}
                            </div>
                            <div>
                              <p className="font-semibold text-dark">
                                {emp.first_name} {emp.last_name}
                              </p>
                              <p className="text-[11px] text-secondary">{emp.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-dark">{emp.employee_code}</td>
                        <td className="py-3 px-4 text-dark font-medium">{emp.department_name || 'General'}</td>
                        <td className="py-3 px-4 text-secondary">{emp.designation}</td>
                        <td className="py-3 px-4 text-secondary font-mono">{emp.date_of_joining}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                              emp.is_active
                                ? 'bg-emerald-50 text-success border-emerald-200'
                                : 'bg-slate-100 text-secondary border-slate-200'
                            }`}
                          >
                            {emp.is_active ? <UserCheck className="w-3 h-3" /> : <UserX className="w-3 h-3" />}
                            <span>{emp.is_active ? 'Active' : 'Inactive'}</span>
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => {
                              setSelectedEmployee(emp);
                              setShowViewModal(true);
                            }}
                            className="p-1.5 rounded text-secondary hover:text-primary transition-colors cursor-pointer"
                            title="View Profile"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ONBOARDING APPROVALS */}
      {activeTab === 'onboarding' && canManageEmployees && (
        <div className="space-y-4">
          <div className="bg-card border border-border rounded-xl p-4 shadow-card flex flex-col sm:flex-row items-center gap-3 justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-secondary">Filter by Status:</span>
              <div className="flex items-center gap-1">
                {(['all', 'pending_approval', 'approved', 'rejected'] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setOnboardingFilter(st)}
                    className={`px-3 py-1 text-xs rounded-lg font-medium transition-colors cursor-pointer ${
                      onboardingFilter === st
                        ? 'bg-primary text-white shadow-xs'
                        : 'bg-slate-50 text-secondary hover:bg-slate-100'
                    }`}
                  >
                    {st === 'all'
                      ? 'All'
                      : st === 'pending_approval'
                      ? 'Pending Approval'
                      : st === 'approved'
                      ? 'Approved'
                      : 'Rejected'}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={fetchOnboardingRequests}
              disabled={onboardingLoading}
              className="px-3 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-50 flex items-center gap-1.5 transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${onboardingLoading ? 'animate-spin text-primary' : 'text-secondary'}`} />
              <span>Refresh</span>
            </button>
          </div>

          <div className="bg-card border border-border rounded-xl shadow-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                    <th className="py-3 px-4">Candidate / Employee</th>
                    <th className="py-3 px-4">Code</th>
                    <th className="py-3 px-4">Department & Role</th>
                    <th className="py-3 px-4">Requested By</th>
                    <th className="py-3 px-4">Requested On</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Authorization Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-medium">
                  {onboardingLoading ? (
                    <tr>
                      <td colSpan={7} className="text-center py-10 text-secondary">
                        Loading onboarding requests...
                      </td>
                    </tr>
                  ) : onboardingRequests.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-10 text-secondary">
                        No onboarding requests found for the selected filter.
                      </td>
                    </tr>
                  ) : (
                    onboardingRequests.map((req) => (
                      <tr key={req.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-indigo-50 text-indigo-700 font-bold flex items-center justify-center text-xs flex-shrink-0 border border-indigo-100">
                              {req.first_name[0]}
                            </div>
                            <div>
                              <p className="font-semibold text-dark">
                                {req.first_name} {req.last_name}
                              </p>
                              <p className="text-[11px] text-secondary">{req.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-mono text-dark">{req.employee_code}</td>
                        <td className="py-3 px-4">
                          <p className="font-semibold text-dark">{req.designation}</p>
                          <p className="text-[11px] text-secondary">{req.department_name || 'General'}</p>
                        </td>
                        <td className="py-3 px-4 text-secondary">{req.requested_by_name || 'HR Manager'}</td>
                        <td className="py-3 px-4 text-secondary font-mono">
                          {req.created_at ? req.created_at.split('T')[0] : req.date_of_joining}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                              req.status === 'approved'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : req.status === 'rejected'
                                ? 'bg-rose-50 text-rose-700 border-rose-200'
                                : 'bg-amber-50 text-amber-700 border-amber-200'
                            }`}
                          >
                            {req.status === 'approved' ? (
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            ) : req.status === 'rejected' ? (
                              <XCircle className="w-3 h-3 text-rose-600" />
                            ) : (
                              <Clock className="w-3 h-3 text-amber-600" />
                            )}
                            <span className="capitalize">{req.status.replace('_', ' ')}</span>
                          </span>
                          {req.rejection_reason && (
                            <p className="text-[10px] text-rose-600 mt-1 max-w-[180px] truncate" title={req.rejection_reason}>
                              Reason: {req.rejection_reason}
                            </p>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          {req.status === 'pending_approval' && isAdmin ? (
                            <div className="flex items-center justify-end gap-1.5">
                              <button
                                onClick={() => handleReviewRequest(req.id, 'approved')}
                                disabled={reviewLoadingId === req.id}
                                className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-md text-[11px] font-medium flex items-center gap-1 transition-colors shadow-xs disabled:opacity-50 cursor-pointer"
                                title="Authorize and Add to Active Directory"
                              >
                                <CheckCircle2 className="w-3 h-3" />
                                <span>Authorize</span>
                              </button>
                              <button
                                onClick={() => {
                                  setRejectRequestId(req.id);
                                  setShowRejectModal(true);
                                }}
                                disabled={reviewLoadingId === req.id}
                                className="px-2.5 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-md text-[11px] font-medium flex items-center gap-1 transition-colors disabled:opacity-50 cursor-pointer"
                                title="Reject Request"
                              >
                                <XCircle className="w-3 h-3" />
                                <span>Reject</span>
                              </button>
                            </div>
                          ) : req.status === 'pending_approval' ? (
                            <span className="text-[11px] text-amber-600 font-medium italic">Awaiting Admin</span>
                          ) : (
                            <span className="text-[11px] text-secondary">Completed</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Add / Request Employee Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-dark">
                  {isAdmin ? 'Add New Employee (Direct Authorization)' : 'Submit Employee Onboarding Request'}
                </h3>
                <p className="text-[11px] text-secondary mt-0.5">
                  {isAdmin
                    ? 'Authorized directly: creates active login credentials and assigns default shift.'
                    : 'Submitted request will be routed to an Administrator for final authorization.'}
                </p>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-secondary hover:text-dark p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateEmployeeRequest} className="p-6 space-y-4">
              {formMsg && (
                <div
                  className={`p-3 rounded-lg text-xs flex items-center gap-2 ${
                    formMsg.error
                      ? 'bg-rose-50 text-rose-800 border border-rose-200'
                      : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  }`}
                >
                  {formMsg.error ? <AlertTriangle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                  <span>{formMsg.text}</span>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">First Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Liam"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Last Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Vance"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Employee Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. EMP305"
                    value={formData.employee_code}
                    onChange={(e) => setFormData({ ...formData, employee_code: e.target.value.toUpperCase() })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark font-mono focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Email Address *</label>
                  <input
                    type="email"
                    required
                    placeholder="e.g. liam.vance@attendai.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Department *</label>
                  <select
                    required
                    value={formData.department_id}
                    onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="">Select Department</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} ({d.code})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Designation *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Operations Specialist"
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Phone Number</label>
                  <input
                    type="text"
                    placeholder="+1 (555) 019-2831"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Date of Joining *</label>
                  <input
                    type="date"
                    required
                    value={formData.date_of_joining}
                    onChange={(e) => setFormData({ ...formData, date_of_joining: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingOnboard}
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
                >
                  {isAdmin ? <ShieldCheck className="w-3.5 h-3.5" /> : <Send className="w-3.5 h-3.5" />}
                  <span>
                    {submittingOnboard
                      ? 'Processing...'
                      : isAdmin
                      ? 'Authorize & Add Employee'
                      : 'Submit Request to Admin'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-sm overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-5 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-xs font-bold text-dark">Reject Onboarding Request</h3>
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectRequestId(null);
                  setRejectionReason('');
                }}
                className="text-secondary hover:text-dark p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-5 space-y-3">
              <p className="text-xs text-secondary">
                Please provide a brief reason for declining this employee onboarding request:
              </p>
              <textarea
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Duplicate profile, missing departmental authorization..."
                className="w-full p-2.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-rose-500"
              />
            </div>
            <div className="px-5 py-3 bg-slate-50 border-t border-border flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectRequestId(null);
                  setRejectionReason('');
                }}
                className="px-3 py-1.5 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (rejectRequestId) {
                    handleReviewRequest(rejectRequestId, 'rejected', rejectionReason);
                  }
                }}
                disabled={reviewLoadingId !== null}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors cursor-pointer disabled:opacity-50"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Employee Profile Modal */}
      {showViewModal && selectedEmployee && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Employee Profile</h3>
              <button
                onClick={() => setShowViewModal(false)}
                className="text-secondary hover:text-dark p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 space-y-4 text-xs">
              <div className="flex items-center gap-3 pb-4 border-b border-border">
                <div className="w-12 h-12 rounded-full bg-primary/10 text-primary font-bold flex items-center justify-center text-base">
                  {selectedEmployee.first_name[0]}
                </div>
                <div>
                  <h4 className="font-bold text-sm text-dark">
                    {selectedEmployee.first_name} {selectedEmployee.last_name}
                  </h4>
                  <p className="text-secondary font-medium">{selectedEmployee.designation}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-secondary">
                <div>
                  <span className="font-semibold text-dark block">Employee Code</span>
                  <span className="font-mono">{selectedEmployee.employee_code}</span>
                </div>
                <div>
                  <span className="font-semibold text-dark block">Department</span>
                  <span>{selectedEmployee.department_name || 'General'}</span>
                </div>
                <div>
                  <span className="font-semibold text-dark block">Email</span>
                  <span>{selectedEmployee.email}</span>
                </div>
                <div>
                  <span className="font-semibold text-dark block">Phone</span>
                  <span>{selectedEmployee.phone || 'N/A'}</span>
                </div>
                <div>
                  <span className="font-semibold text-dark block">Date of Joining</span>
                  <span className="font-mono">{selectedEmployee.date_of_joining}</span>
                </div>
                <div>
                  <span className="font-semibold text-dark block">Current Shift</span>
                  <span>{selectedEmployee.current_shift || 'General Shift (09:00 - 17:00)'}</span>
                </div>
              </div>
            </div>
            <div className="px-6 py-3 bg-slate-50 border-t border-border flex justify-end">
              <button
                onClick={() => setShowViewModal(false)}
                className="px-4 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-100 cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Custom Report Builder Modal */}
      <CustomReportModal
        isOpen={showReportModal}
        onClose={() => setShowReportModal(false)}
        initialReportType="workforce_complete"
        onOpenHistory={() => {
          setShowReportModal(false);
          setShowHistoryModal(true);
        }}
      />

      {/* Export History Modal */}
      <ExportHistoryModal
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        onOpenReportBuilder={() => {
          setShowHistoryModal(false);
          setShowReportModal(true);
        }}
      />
    </div>
  );
};
