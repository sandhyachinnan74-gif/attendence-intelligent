import React, { useEffect, useState } from 'react';
import { Plus, Search, Filter, Mail, Phone, Building2, UserCheck, UserX, Edit, Eye, X } from 'lucide-react';
import { api } from '../services/api';
import { Employee, Department } from '../types';
import { useAuth } from '../context/AuthContext';

export const Employees: React.FC = () => {
  const { user } = useAuth();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [loading, setLoading] = useState(true);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | null>(null);
  const [showViewModal, setShowViewModal] = useState(false);

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

  useEffect(() => {
    fetchDepartments();
  }, []);

  useEffect(() => {
    fetchEmployees();
  }, [search, selectedDept]);

  const handleCreateEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/employees', formData);
      setShowAddModal(false);
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
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create employee');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Employee Directory</h1>
          <p className="text-xs text-secondary mt-0.5">Manage workforce profiles, department mapping and status.</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="px-3.5 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Employee</span>
        </button>
      </div>

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
                        className="p-1 rounded text-secondary hover:text-primary transition-colors"
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

      {/* Add Employee Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Create New Employee</h3>
              <button onClick={() => setShowAddModal(false)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateEmployee} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">First Name</label>
                  <input
                    type="text"
                    required
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Last Name</label>
                  <input
                    type="text"
                    required
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Employee Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. EMP201"
                    value={formData.employee_code}
                    onChange={(e) => setFormData({ ...formData, employee_code: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Department</label>
                  <select
                    value={formData.department_id}
                    onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  >
                    <option value="">Select Department</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Designation</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Software Engineer"
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Phone</label>
                  <input
                    type="text"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-dark mb-1">Date of Joining</label>
                  <input
                    type="date"
                    required
                    value={formData.date_of_joining}
                    onChange={(e) => setFormData({ ...formData, date_of_joining: e.target.value })}
                    className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm"
                >
                  Save Employee
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Employee Profile Modal */}
      {showViewModal && selectedEmployee && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Employee Profile</h3>
              <button onClick={() => setShowViewModal(false)} className="text-secondary hover:text-dark">
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
                className="px-4 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-100"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
