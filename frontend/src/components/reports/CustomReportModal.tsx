import React, { useState, useEffect } from 'react';
import {
  X,
  FileSpreadsheet,
  FileText,
  ChevronRight,
  ChevronLeft,
  Check,
  Building2,
  Users,
  User,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Layers,
  Clock,
  Search,
  Sliders,
  History,
  RotateCcw
} from 'lucide-react';
import { api } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { downloadFile } from '../../utils/download';

interface CustomReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialReportType?: string;
  initialDepartmentId?: string;
  initialEmployeeId?: string;
  initialStartDate?: string;
  initialEndDate?: string;
  onOpenHistory?: () => void;
}

export const CustomReportModal: React.FC<CustomReportModalProps> = ({
  isOpen,
  onClose,
  initialReportType,
  initialDepartmentId,
  initialEmployeeId,
  initialStartDate,
  initialEndDate,
  onOpenHistory
}) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const isHR = user?.role === 'hr_manager';
  const isEmployee = user?.role === 'employee';

  const [step, setStep] = useState<number>(1);
  const [loadingConfig, setLoadingConfig] = useState<boolean>(true);

  // Config data from backend
  const [reportTypes, setReportTypes] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [columnsMap, setColumnsMap] = useState<Record<string, any[]>>({});

  // Selection states
  // Step 1: Report Type
  const [selectedReportType, setSelectedReportType] = useState<string>('');
  const [reportTypeSearch, setReportTypeSearch] = useState<string>('');

  // Step 2: Scope
  const [scopeType, setScopeType] = useState<string>('organization');
  const [selectedDeptIds, setSelectedDeptIds] = useState<string[]>([]);
  const [selectedEmpIds, setSelectedEmpIds] = useState<string[]>([]);
  const [deptSearch, setDeptSearch] = useState<string>('');
  const [empSearch, setEmpSearch] = useState<string>('');

  // Step 3: Date Range & Filters
  const [datePreset, setDatePreset] = useState<string>('this_month');
  const [startDate, setStartDate] = useState<string>(initialStartDate || '');
  const [endDate, setEndDate] = useState<string>(initialEndDate || '');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [minLateMinutes, setMinLateMinutes] = useState<string>('');
  const [minOvertimeHours, setMinOvertimeHours] = useState<string>('');

  // Step 4: Format
  const [format, setFormat] = useState<'csv' | 'xlsx'>('xlsx');

  // Step 5: Columns
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);

  // Step 6: Preview & Generation
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<any | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const [generating, setGenerating] = useState<boolean>(false);
  const [generationProgress, setGenerationProgress] = useState<string>('');
  const [generatedResult, setGeneratedResult] = useState<any | null>(null);
  const [generateError, setGenerateError] = useState<string | null>(null);

  // Load config on modal open
  useEffect(() => {
    if (!isOpen) return;

    const fetchConfig = async () => {
      setLoadingConfig(true);
      try {
        const res = await api.get('/exports/config');
        const data = res.data;
        setReportTypes(data.report_types || []);
        setDepartments(data.departments || []);
        setEmployees(data.employees || []);
        setColumnsMap(data.columns_map || {});

        // Pick initial report type
        const defaultType =
          initialReportType ||
          (data.report_types.length > 0 ? data.report_types[0].id : '');
        setSelectedReportType(defaultType);

        // Prepopulate default columns for that report type
        const availableCols = data.columns_map[defaultType] || [];
        const defColIds = availableCols
          .filter((c: any) => c.is_default)
          .map((c: any) => c.id);
        setSelectedColumns(defColIds.length > 0 ? defColIds : availableCols.map((c: any) => c.id));

        // Initial scope
        if (isEmployee) {
          setScopeType('personal');
        } else if (initialEmployeeId) {
          setScopeType('individual_employee');
          setSelectedEmpIds([initialEmployeeId]);
        } else if (initialDepartmentId) {
          setScopeType('department');
          setSelectedDeptIds([initialDepartmentId]);
        } else {
          setScopeType('organization');
        }
      } catch (err) {
        console.error('Failed to load export config:', err);
      } finally {
        setLoadingConfig(false);
      }
    };

    fetchConfig();
    setStep(1);
    setGeneratedResult(null);
    setGenerateError(null);
  }, [isOpen, initialReportType, initialDepartmentId, initialEmployeeId]);

  // When report type changes, sync available columns
  const handleSelectReportType = (rtId: string) => {
    setSelectedReportType(rtId);
    const available = columnsMap[rtId] || [];
    const defaultIds = available
      .filter((c: any) => c.is_default)
      .map((c: any) => c.id);
    setSelectedColumns(defaultIds.length > 0 ? defaultIds : available.map((c: any) => c.id));
  };

  // Fetch Preview when reaching Step 6
  const fetchPreview = async () => {
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const payload = {
        report_type: selectedReportType,
        scope_type: isEmployee ? 'personal' : scopeType,
        department_ids: selectedDeptIds.length > 0 ? selectedDeptIds : undefined,
        employee_ids: selectedEmpIds.length > 0 ? selectedEmpIds : undefined,
        date_preset: datePreset,
        start_date: datePreset === 'custom' && startDate ? startDate : undefined,
        end_date: datePreset === 'custom' && endDate ? endDate : undefined,
        columns: selectedColumns,
        filters: {
          status: statusFilter || undefined,
          min_late_minutes: minLateMinutes ? parseInt(minLateMinutes) : undefined,
          min_overtime_hours: minOvertimeHours ? parseFloat(minOvertimeHours) : undefined,
        },
        format: format,
      };
      const res = await api.post('/exports/preview', payload);
      setPreviewData(res.data);
    } catch (err: any) {
      setPreviewError(err.response?.data?.detail || 'Failed to calculate report preview.');
    } finally {
      setPreviewLoading(false);
    }
  };

  useEffect(() => {
    if (step === 6) {
      fetchPreview();
    }
  }, [step]);

  // Execute Generation and Immediate Download
  const handleGenerateAndDownload = async () => {
    setGenerating(true);
    setGenerateError(null);
    setGenerationProgress('Querying authorized database records...');

    try {
      setTimeout(() => setGenerationProgress(`Rendering formatted ${format.toUpperCase()} document...`), 300);

      const payload = {
        report_type: selectedReportType,
        scope_type: isEmployee ? 'personal' : scopeType,
        department_ids: selectedDeptIds.length > 0 ? selectedDeptIds : undefined,
        employee_ids: selectedEmpIds.length > 0 ? selectedEmpIds : undefined,
        date_preset: datePreset,
        start_date: datePreset === 'custom' && startDate ? startDate : undefined,
        end_date: datePreset === 'custom' && endDate ? endDate : undefined,
        columns: selectedColumns,
        filters: {
          status: statusFilter || undefined,
          min_late_minutes: minLateMinutes ? parseInt(minLateMinutes) : undefined,
          min_overtime_hours: minOvertimeHours ? parseFloat(minOvertimeHours) : undefined,
        },
        format: format,
      };

      const res = await api.post('/exports/generate', payload);
      setGeneratedResult(res.data);

      // Automatically trigger browser download with authentic filename
      const downloadUrl = res.data.download_url;
      const ext = res.data.format;
      const filename = `${res.data.report_name.replace(/ /g, '_')}.${ext}`;
      await downloadFile(downloadUrl, filename);
    } catch (err: any) {
      setGenerateError(err.response?.data?.detail || 'Report generation failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadAgain = () => {
    if (!generatedResult) return;
    const downloadUrl = generatedResult.download_url;
    const ext = generatedResult.format;
    const filename = `${generatedResult.report_name.replace(/ /g, '_')}.${ext}`;
    downloadFile(downloadUrl, filename);
  };

  if (!isOpen) return null;

  const currentAvailableCols = columnsMap[selectedReportType] || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-white border border-border rounded-2xl shadow-2xl w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden my-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-slate-50/75">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
              <Download className="w-5 h-5 text-primary" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-dark tracking-tight">What would you like to download?</h2>
                <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-50 text-primary border border-blue-200">
                  Step {step} of 6
                </span>
              </div>
              <p className="text-xs text-secondary mt-0.5">
                Select document type, data scope, date range, file format and columns.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {onOpenHistory && (
              <button
                onClick={() => {
                  onClose();
                  onOpenHistory();
                }}
                className="px-2.5 py-1.5 text-xs text-secondary hover:text-dark hover:bg-slate-200/60 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
                title="View past generated reports"
              >
                <History className="w-3.5 h-3.5 text-primary" />
                <span className="hidden sm:inline">Export History</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 text-secondary hover:text-dark hover:bg-slate-200/60 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Stepper Progress Bar */}
        <div className="bg-white px-6 py-2.5 border-b border-border/80 overflow-x-auto">
          <div className="flex items-center justify-between min-w-[550px] text-xs">
            {[
              { num: 1, label: 'Document Type' },
              { num: 2, label: 'Data Scope' },
              { num: 3, label: 'Date Range' },
              { num: 4, label: 'File Format' },
              { num: 5, label: 'Select Columns' },
              { num: 6, label: 'Preview & Download' },
            ].map((s) => (
              <button
                key={s.num}
                onClick={() => {
                  if (s.num < step || (!generatedResult && s.num <= step)) {
                    setStep(s.num);
                  }
                }}
                disabled={generating || (generatedResult !== null && s.num !== 6)}
                className={`flex items-center gap-2 pb-1 font-medium transition-colors cursor-pointer ${
                  step === s.num
                    ? 'text-primary font-bold border-b-2 border-primary'
                    : s.num < step
                    ? 'text-emerald-700 hover:text-emerald-800'
                    : 'text-secondary/60 hover:text-secondary'
                }`}
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    step === s.num
                      ? 'bg-primary text-white shadow-xs'
                      : s.num < step
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-slate-100 text-slate-500'
                  }`}
                >
                  {s.num < step ? <Check className="w-3 h-3 text-emerald-700" /> : s.num}
                </span>
                <span>{s.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Modal Body Content */}
        <div className="flex-1 overflow-y-auto p-6 text-xs text-dark space-y-6">
          {loadingConfig ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-3">
              <RefreshCw className="w-7 h-7 text-primary animate-spin" />
              <p className="text-xs text-secondary font-medium">Loading report options and authorized scopes...</p>
            </div>
          ) : (
            <>
              {/* STEP 1: SELECT DOCUMENT / REPORT TYPE */}
              {step === 1 && (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-bold text-dark">Step 1 — Select Document / Report Type</h3>
                      <p className="text-xs text-secondary mt-0.5">
                        {isEmployee
                          ? 'Choose the personal record or summary you would like to export.'
                          : 'Choose from authorized organization, workforce, attendance and compliance reports.'}
                      </p>
                    </div>
                    <div className="relative w-full sm:w-64">
                      <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-secondary" />
                      <input
                        type="text"
                        placeholder="Search report types..."
                        value={reportTypeSearch}
                        onChange={(e) => setReportTypeSearch(e.target.value)}
                        className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-border rounded-lg text-xs focus:bg-white focus:border-primary"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[420px] overflow-y-auto pr-1">
                    {reportTypes
                      .filter((rt) =>
                        rt.name.toLowerCase().includes(reportTypeSearch.toLowerCase()) ||
                        (rt.desc && rt.desc.toLowerCase().includes(reportTypeSearch.toLowerCase()))
                      )
                      .map((rt) => {
                        const isSelected = selectedReportType === rt.id;
                        return (
                          <div
                            key={rt.id}
                            onClick={() => handleSelectReportType(rt.id)}
                            className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                              isSelected
                                ? 'bg-blue-50/70 border-primary ring-2 ring-primary/20 shadow-xs'
                                : 'bg-white border-border hover:border-slate-300 hover:bg-slate-50/50'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <span className="inline-block text-[10px] uppercase font-bold tracking-wider text-primary mb-1">
                                  {rt.category || 'General'}
                                </span>
                                <h4 className="text-xs font-bold text-dark">{rt.name}</h4>
                                <p className="text-[11px] text-secondary mt-1 leading-relaxed">
                                  {rt.desc}
                                </p>
                              </div>
                              <div
                                className={`w-4 h-4 rounded-full border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                                  isSelected
                                    ? 'bg-primary border-primary text-white'
                                    : 'border-slate-300 bg-white'
                                }`}
                              >
                                {isSelected && <Check className="w-2.5 h-2.5" />}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}

              {/* STEP 2: SELECT DATA SCOPE */}
              {step === 2 && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-dark">Step 2 — Select Data Scope</h3>
                    <p className="text-xs text-secondary mt-0.5">
                      Define the target organizational unit, department, or employees included in this report.
                    </p>
                  </div>

                  {/* Employee: personal lock */}
                  {isEmployee ? (
                    <div className="p-5 rounded-xl bg-slate-50 border border-border flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
                        <User className="w-5 h-5" />
                      </div>
                      <div className="space-y-1">
                        <span className="inline-block px-2.5 py-0.5 bg-blue-100 text-primary rounded-full text-[10px] font-bold">
                          Personal Records Only
                        </span>
                        <h4 className="text-xs font-bold text-dark">
                          {user?.first_name} {user?.last_name} ({user?.email})
                        </h4>
                        <p className="text-[11px] text-secondary leading-relaxed">
                          As an Employee, your report automatically includes your verified personal attendance records,
                          shifts, and leave history. Organizational data protection policies automatically prevent
                          department or peer data access.
                        </p>
                      </div>
                    </div>
                  ) : (
                    /* Admin & HR Scope Selectors */
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {/* Scope Option 1: Entire Org / Authorized Workforce */}
                        <div
                          onClick={() => {
                            setScopeType('organization');
                            setSelectedDeptIds([]);
                            setSelectedEmpIds([]);
                          }}
                          className={`p-4 rounded-xl border cursor-pointer transition-all ${
                            scopeType === 'organization'
                              ? 'bg-blue-50/70 border-primary ring-2 ring-primary/20 shadow-xs'
                              : 'bg-white border-border hover:border-slate-300'
                          }`}
                        >
                          <Building2 className="w-5 h-5 text-primary mb-2" />
                          <h4 className="text-xs font-bold text-dark">
                            {isAdmin ? 'Entire Organization' : 'Authorized Workforce'}
                          </h4>
                          <p className="text-[11px] text-secondary mt-1">
                            {isAdmin
                              ? 'Includes all departments, divisions and active employees.'
                              : 'Includes all employees within your authorized HR jurisdiction.'}
                          </p>
                        </div>

                        {/* Scope Option 2: Departments */}
                        <div
                          onClick={() => {
                            setScopeType('department');
                            if (departments.length > 0 && selectedDeptIds.length === 0) {
                              setSelectedDeptIds([departments[0].id]);
                            }
                          }}
                          className={`p-4 rounded-xl border cursor-pointer transition-all ${
                            scopeType === 'department' || scopeType === 'multi_department'
                              ? 'bg-blue-50/70 border-primary ring-2 ring-primary/20 shadow-xs'
                              : 'bg-white border-border hover:border-slate-300'
                          }`}
                        >
                          <Users className="w-5 h-5 text-indigo-600 mb-2" />
                          <h4 className="text-xs font-bold text-dark">Department(s)</h4>
                          <p className="text-[11px] text-secondary mt-1">
                            Filter by one specific department or multiple selected departments.
                          </p>
                        </div>

                        {/* Scope Option 3: Individual / Multiple Employees */}
                        <div
                          onClick={() => {
                            setScopeType('individual_employee');
                            if (employees.length > 0 && selectedEmpIds.length === 0) {
                              setSelectedEmpIds([employees[0].id]);
                            }
                          }}
                          className={`p-4 rounded-xl border cursor-pointer transition-all ${
                            scopeType === 'individual_employee' || scopeType === 'multi_employee'
                              ? 'bg-blue-50/70 border-primary ring-2 ring-primary/20 shadow-xs'
                              : 'bg-white border-border hover:border-slate-300'
                          }`}
                        >
                          <User className="w-5 h-5 text-emerald-600 mb-2" />
                          <h4 className="text-xs font-bold text-dark">Employee(s)</h4>
                          <p className="text-[11px] text-secondary mt-1">
                            Filter by a single employee or select multiple individuals.
                          </p>
                        </div>
                      </div>

                      {/* Department Selectors */}
                      {(scopeType === 'department' || scopeType === 'multi_department') && (
                        <div className="p-4 bg-slate-50 border border-border rounded-xl space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-dark text-xs">
                              Select Departments ({selectedDeptIds.length} chosen)
                            </span>
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => setSelectedDeptIds(departments.map((d) => d.id))}
                                className="text-[11px] text-primary hover:underline font-medium cursor-pointer"
                              >
                                Select All
                              </button>
                              <span className="text-secondary">&bull;</span>
                              <button
                                type="button"
                                onClick={() => setSelectedDeptIds([])}
                                className="text-[11px] text-secondary hover:underline font-medium cursor-pointer"
                              >
                                Clear
                              </button>
                            </div>
                          </div>

                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
                            {departments.map((d) => {
                              const checked = selectedDeptIds.includes(d.id);
                              return (
                                <label
                                  key={d.id}
                                  className={`p-2.5 rounded-lg border flex items-center gap-2 cursor-pointer transition-colors ${
                                    checked
                                      ? 'bg-blue-50 border-primary font-bold text-dark'
                                      : 'bg-white border-border text-secondary hover:bg-slate-100'
                                  }`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={(e) => {
                                      if (e.target.checked) {
                                        setSelectedDeptIds([...selectedDeptIds, d.id]);
                                      } else {
                                        setSelectedDeptIds(selectedDeptIds.filter((id) => id !== d.id));
                                      }
                                    }}
                                    className="rounded border-border text-primary focus:ring-primary"
                                  />
                                  <span className="truncate">{d.name} ({d.code})</span>
                                </label>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Employee Selectors */}
                      {(scopeType === 'individual_employee' || scopeType === 'multi_employee') && (
                        <div className="p-4 bg-slate-50 border border-border rounded-xl space-y-3">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <span className="font-bold text-dark text-xs">
                              Select Employees ({selectedEmpIds.length} chosen)
                            </span>
                            <div className="relative w-full sm:w-56">
                              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-secondary" />
                              <input
                                type="text"
                                placeholder="Search employees..."
                                value={empSearch}
                                onChange={(e) => setEmpSearch(e.target.value)}
                                className="w-full pl-7 pr-2 py-1 bg-white border border-border rounded text-[11px]"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto">
                            {employees
                              .filter((e) =>
                                e.name.toLowerCase().includes(empSearch.toLowerCase()) ||
                                e.code.toLowerCase().includes(empSearch.toLowerCase())
                              )
                              .map((e) => {
                                const checked = selectedEmpIds.includes(e.id);
                                return (
                                  <label
                                    key={e.id}
                                    className={`p-2 rounded-lg border flex items-center justify-between gap-2 cursor-pointer transition-colors ${
                                      checked
                                        ? 'bg-blue-50 border-primary font-bold text-dark'
                                        : 'bg-white border-border text-secondary hover:bg-slate-100'
                                    }`}
                                  >
                                    <div className="flex items-center gap-2 overflow-hidden">
                                      <input
                                        type="checkbox"
                                        checked={checked}
                                        onChange={(ev) => {
                                          if (ev.target.checked) {
                                            setSelectedEmpIds([...selectedEmpIds, e.id]);
                                          } else {
                                            setSelectedEmpIds(selectedEmpIds.filter((id) => id !== e.id));
                                          }
                                        }}
                                        className="rounded border-border text-primary focus:ring-primary"
                                      />
                                      <div className="truncate">
                                        <p className="text-xs truncate">{e.name}</p>
                                        <p className="text-[10px] text-secondary truncate">{e.code} &bull; {e.designation}</p>
                                      </div>
                                    </div>
                                  </label>
                                );
                              })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* STEP 3: SELECT DATE RANGE & FILTERS */}
              {step === 3 && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-dark">Step 3 — Select Date Range & Filters</h3>
                    <p className="text-xs text-secondary mt-0.5">
                      Select reporting time windows, punctuality thresholds and status filters.
                    </p>
                  </div>

                  {/* Preset Pills */}
                  <div className="space-y-2">
                    <label className="block text-xs font-bold text-dark">Date Period Preset</label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-2">
                      {[
                        { id: 'today', label: 'Today' },
                        { id: 'yesterday', label: 'Yesterday' },
                        { id: 'this_week', label: 'This Week' },
                        { id: 'last_week', label: 'Last Week' },
                        { id: 'this_month', label: 'This Month' },
                        { id: 'last_month', label: 'Last Month' },
                        { id: 'last_7_days', label: 'Last 7 Days' },
                        { id: 'last_30_days', label: 'Last 30 Days' },
                        { id: 'last_90_days', label: 'Last 90 Days' },
                        { id: 'custom', label: 'Custom Date Range' },
                      ].map((p) => {
                        const active = datePreset === p.id;
                        return (
                          <button
                            key={p.id}
                            type="button"
                            onClick={() => setDatePreset(p.id)}
                            className={`px-3 py-2 rounded-lg border text-xs font-semibold text-center transition-all cursor-pointer ${
                              active
                                ? 'bg-primary text-white border-primary shadow-xs'
                                : 'bg-white text-secondary border-border hover:bg-slate-50 hover:text-dark'
                            }`}
                          >
                            {p.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Custom Date Inputs */}
                  {datePreset === 'custom' && (
                    <div className="p-4 bg-slate-50 border border-border rounded-xl space-y-3">
                      <span className="font-bold text-dark text-xs block">Specify Custom Range</span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block font-medium text-secondary mb-1">Start Date</label>
                          <input
                            type="date"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full px-3 py-1.5 bg-white border border-border rounded-lg text-dark"
                          />
                        </div>
                        <div>
                          <label className="block font-medium text-secondary mb-1">End Date</label>
                          <input
                            type="date"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full px-3 py-1.5 bg-white border border-border rounded-lg text-dark"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Optional Status & Threshold Filters */}
                  <div className="p-4 bg-slate-50 border border-border rounded-xl space-y-3">
                    <span className="font-bold text-dark text-xs block">Additional Parameter Filters (Optional)</span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div>
                        <label className="block font-medium text-secondary mb-1">Attendance Status</label>
                        <select
                          value={statusFilter}
                          onChange={(e) => setStatusFilter(e.target.value)}
                          className="w-full px-3 py-1.5 bg-white border border-border rounded-lg text-dark"
                        >
                          <option value="">All Statuses</option>
                          <option value="present">Present</option>
                          <option value="late">Late Arrival</option>
                          <option value="half_day">Half Day</option>
                          <option value="absent">Absent</option>
                        </select>
                      </div>

                      <div>
                        <label className="block font-medium text-secondary mb-1">Minimum Late Threshold (Mins)</label>
                        <input
                          type="number"
                          min="0"
                          placeholder="e.g. 15"
                          value={minLateMinutes}
                          onChange={(e) => setMinLateMinutes(e.target.value)}
                          className="w-full px-3 py-1.5 bg-white border border-border rounded-lg text-dark"
                        />
                      </div>

                      <div>
                        <label className="block font-medium text-secondary mb-1">Minimum Overtime (Hours)</label>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          placeholder="e.g. 1.0"
                          value={minOvertimeHours}
                          onChange={(e) => setMinOvertimeHours(e.target.value)}
                          className="w-full px-3 py-1.5 bg-white border border-border rounded-lg text-dark"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 4: SELECT FILE FORMAT */}
              {step === 4 && (
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-dark">Step 4 — Select File Format</h3>
                    <p className="text-xs text-secondary mt-0.5">
                      Choose the preferred document output format. Both options generate authentic, production files.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    {/* CSV Card */}
                    <div
                      onClick={() => setFormat('csv')}
                      className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                        format === 'csv'
                          ? 'bg-blue-50/70 border-primary shadow-md ring-2 ring-primary/20'
                          : 'bg-white border-border hover:border-slate-300 hover:shadow-xs'
                      }`}
                    >
                      <div className="w-12 h-12 rounded-xl bg-blue-100 text-primary flex items-center justify-center mb-3">
                        <FileText className="w-6 h-6" />
                      </div>
                      <h4 className="text-sm font-bold text-dark">CSV (.csv)</h4>
                      <p className="text-xs text-secondary mt-1 leading-relaxed">
                        Simple spreadsheet-compatible data. Clean UTF-8 tabular data with universal importing compatibility.
                      </p>
                      <span className="inline-block mt-3 px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-100 text-blue-800">
                        Spreadsheet Compatible
                      </span>
                    </div>

                    {/* Excel Card */}
                    <div
                      onClick={() => setFormat('xlsx')}
                      className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                        format === 'xlsx'
                          ? 'bg-emerald-50/70 border-emerald-500 shadow-md ring-2 ring-emerald-500/20'
                          : 'bg-white border-border hover:border-slate-300 hover:shadow-xs'
                      }`}
                    >
                      <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-3">
                        <FileSpreadsheet className="w-6 h-6" />
                      </div>
                      <h4 className="text-sm font-bold text-dark">Excel (.xlsx)</h4>
                      <p className="text-xs text-secondary mt-1 leading-relaxed">
                        Formatted workbook with headers, filters and worksheets. Structured workbook using openpyxl.
                      </p>
                      <span className="inline-block mt-3 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                        Formatted Workbook
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 5: SELECT COLUMNS */}
              {step === 5 && (
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <h3 className="text-sm font-bold text-dark">Step 5 — Select Information & Columns</h3>
                      <p className="text-xs text-secondary mt-0.5">
                        Customize which fields are included in the generated output ({selectedColumns.length} of{' '}
                        {currentAvailableCols.length} selected).
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setSelectedColumns(currentAvailableCols.map((c) => c.id))}
                        className="px-2.5 py-1 text-xs font-semibold text-primary bg-primary/10 hover:bg-primary/20 rounded-md transition-colors cursor-pointer"
                      >
                        Select All
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          const defIds = currentAvailableCols.filter((c) => c.is_default).map((c) => c.id);
                          setSelectedColumns(defIds.length > 0 ? defIds : currentAvailableCols.map((c) => c.id));
                        }}
                        className="px-2.5 py-1 text-xs font-semibold text-secondary hover:text-dark border border-border rounded-md hover:bg-slate-50 transition-colors cursor-pointer flex items-center gap-1"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Restore Defaults</span>
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 max-h-[420px] overflow-y-auto pr-1">
                    {currentAvailableCols.map((col) => {
                      const isChecked = selectedColumns.includes(col.id);
                      return (
                        <label
                          key={col.id}
                          className={`p-3 rounded-xl border flex items-center gap-2.5 cursor-pointer transition-all ${
                            isChecked
                              ? 'bg-blue-50/60 border-primary font-bold text-dark'
                              : 'bg-white border-border text-secondary hover:bg-slate-50 hover:text-dark'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedColumns([...selectedColumns, col.id]);
                              } else {
                                setSelectedColumns(selectedColumns.filter((id) => id !== col.id));
                              }
                            }}
                            className="rounded border-border text-primary focus:ring-primary w-4 h-4"
                          />
                          <div className="overflow-hidden">
                            <span className="text-xs block truncate">{col.label}</span>
                            {col.is_default && (
                              <span className="text-[9px] uppercase tracking-wider text-primary block">
                                Default Field
                              </span>
                            )}
                          </div>
                        </label>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* STEP 6: PREVIEW BEFORE DOWNLOAD */}
              {step === 6 && (
                <div className="space-y-5">
                  <div>
                    <h3 className="text-sm font-bold text-dark">Step 6 — Preview Before Download</h3>
                    <p className="text-xs text-secondary mt-0.5">
                      Verify report specifications and matching record count before generating.
                    </p>
                  </div>

                  {/* Summary Preview Box */}
                  {previewLoading ? (
                    <div className="p-8 rounded-xl bg-white border border-border flex flex-col items-center justify-center space-y-2">
                      <RefreshCw className="w-6 h-6 text-primary animate-spin" />
                      <p className="text-xs text-secondary font-medium">Fetching authorized matching record count...</p>
                    </div>
                  ) : previewError ? (
                    <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      <span>{previewError}</span>
                    </div>
                  ) : (
                    <div className="bg-white border border-border rounded-xl p-5 shadow-xs space-y-4">
                      <div className="flex items-center justify-between pb-3 border-b border-border">
                        <div>
                          <span className="text-[10px] font-bold uppercase tracking-wider text-primary block">
                            REPORT SPECIFICATION
                          </span>
                          <h4 className="text-base font-bold text-dark mt-0.5">
                            {previewData?.report_title || 'Attendance Report'}
                          </h4>
                        </div>
                        <span className="px-3 py-1 rounded-full text-xs font-bold uppercase bg-slate-100 text-dark border border-slate-200">
                          {format.toUpperCase()}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-secondary block font-medium">Data Scope</span>
                          <span className="font-bold text-dark block mt-0.5 truncate" title={previewData?.scope_summary}>
                            {previewData?.scope_summary || 'Organization'}
                          </span>
                        </div>

                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-secondary block font-medium">Date Range</span>
                          <span className="font-bold text-dark block mt-0.5">
                            {previewData?.start_date} – {previewData?.end_date}
                          </span>
                        </div>

                        <div className="p-3 bg-slate-50 rounded-lg">
                          <span className="text-secondary block font-medium">Selected Columns</span>
                          <span className="font-bold text-dark block mt-0.5">
                            {selectedColumns.length} fields included
                          </span>
                        </div>

                        <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg">
                          <span className="text-primary block font-bold">Matching Records</span>
                          <span className="text-xl font-extrabold text-primary block mt-0.5">
                            {previewData?.record_count ?? 0}
                          </span>
                        </div>
                      </div>

                      {/* Generation Result Banner if complete */}
                      {generatedResult && (
                        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row items-center justify-between gap-3 animate-in fade-in duration-200">
                          <div className="flex items-center gap-3">
                            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
                            <div>
                              <p className="text-xs font-bold text-emerald-900">
                                File generated and downloaded successfully!
                              </p>
                              <p className="text-[11px] text-emerald-700">
                                File Size: {Math.round((generatedResult.file_size_bytes / 1024) * 10) / 10} KB &bull;{' '}
                                Records: {generatedResult.record_count}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={handleDownloadAgain}
                              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all transform active:scale-95 cursor-pointer"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Download Again</span>
                            </button>
                            <button
                              onClick={() => {
                                setGeneratedResult(null);
                                setStep(1);
                              }}
                              className="px-3 py-2 bg-white border border-emerald-300 text-emerald-800 hover:bg-emerald-100 rounded-lg text-xs font-semibold cursor-pointer"
                            >
                              New Report
                            </button>
                          </div>
                        </div>
                      )}

                      {generateError && (
                        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-2">
                          <AlertCircle className="w-4 h-4" />
                          <span>{generateError}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer Controls */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-border flex items-center justify-between">
          <div>
            {step > 1 && !generatedResult && (
              <button
                type="button"
                onClick={() => setStep(step - 1)}
                disabled={generating}
                className="px-3.5 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-secondary hover:text-dark hover:bg-slate-100 flex items-center gap-1 transition-colors cursor-pointer disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={generating}
              className="px-4 py-1.5 border border-border bg-white rounded-lg text-xs font-medium text-secondary hover:text-dark hover:bg-slate-100 cursor-pointer disabled:opacity-50"
            >
              Cancel
            </button>

            {step < 6 && (
              <button
                type="button"
                onClick={() => setStep(step + 1)}
                disabled={loadingConfig || (step === 5 && selectedColumns.length === 0)}
                className="px-4 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-all cursor-pointer disabled:opacity-50"
              >
                <span>Continue</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            )}

            {step === 6 && !generatedResult && (
              <button
                type="button"
                onClick={handleGenerateAndDownload}
                disabled={generating || previewLoading}
                className="px-5 py-2 bg-primary text-white rounded-lg text-xs font-bold hover:bg-primary-hover flex items-center gap-2 shadow-md transition-all transform active:scale-95 cursor-pointer disabled:opacity-50"
              >
                {generating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>{generationProgress || 'Generating & Downloading...'}</span>
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4" />
                    <span>Generate & Download</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
