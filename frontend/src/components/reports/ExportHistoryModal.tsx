import React, { useState, useEffect } from 'react';
import {
  X,
  History,
  Download,
  RefreshCw,
  FileSpreadsheet,
  FileText,
  Printer,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight
} from 'lucide-react';
import { api } from '../../services/api';
import { downloadFile } from '../../utils/download';

interface ExportHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenReportBuilder?: () => void;
}

export const ExportHistoryModal: React.FC<ExportHistoryModalProps> = ({
  isOpen,
  onClose,
  onOpenReportBuilder,
}) => {
  const [historyItems, setHistoryItems] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await api.get('/exports/history');
      setHistoryItems(res.data);
    } catch (err) {
      console.error('Failed to load export history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen]);

  const handleDownload = async (item: any) => {
    setDownloadingId(item.id);
    const filename = `${item.report_name.toLowerCase().replace(/ /g, '_')}.${item.format}`;
    await downloadFile(item.download_url, filename);
    setDownloadingId(null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-white border border-border rounded-2xl shadow-2xl w-full max-w-4xl max-h-[88vh] flex flex-col overflow-hidden my-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-slate-50/75">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center flex-shrink-0">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-dark tracking-tight">Export Management & History</h2>
              <p className="text-xs text-secondary mt-0.5">
                Review and re-download previously generated custom workforce reports.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchHistory}
              disabled={loading}
              className="p-1.5 text-secondary hover:text-dark hover:bg-slate-200/60 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
              title="Refresh History"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-primary' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-secondary hover:text-dark hover:bg-slate-200/60 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Table */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/20">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <RefreshCw className="w-7 h-7 text-primary animate-spin" />
              <p className="text-xs text-secondary font-medium">Loading export history...</p>
            </div>
          ) : historyItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 space-y-3 text-center">
              <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-secondary">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-dark">No reports generated yet</p>
              <p className="text-xs text-secondary max-w-sm">
                You have not created any custom reports in this session. Click below to configure your first export.
              </p>
              {onOpenReportBuilder && (
                <button
                  onClick={() => {
                    onClose();
                    onOpenReportBuilder();
                  }}
                  className="mt-2 px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                >
                  <span>Create Custom Report</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ) : (
            <div className="bg-white border border-border rounded-xl shadow-xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                      <th className="py-3 px-4">Report Details</th>
                      <th className="py-3 px-4">Data Scope</th>
                      <th className="py-3 px-4">Date Range</th>
                      <th className="py-3 px-4">Format</th>
                      <th className="py-3 px-4">Records</th>
                      <th className="py-3 px-4">Size</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border font-medium">
                    {historyItems.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3 px-4">
                          <p className="font-bold text-dark">{item.report_name}</p>
                          <span className="text-[10px] text-secondary font-mono">
                            {new Date(item.created_at).toLocaleString([], {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className="text-dark truncate block max-w-[160px]" title={item.scope_summary}>
                            {item.scope_summary || 'Organization'}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-secondary text-[11px]">
                          {item.start_date} – {item.end_date}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                              item.format === 'xlsx'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : item.format === 'csv'
                                ? 'bg-blue-50 text-primary border-blue-200'
                                : 'bg-rose-50 text-rose-700 border-rose-200'
                            }`}
                          >
                            {item.format}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-semibold text-dark">{item.record_count}</td>
                        <td className="py-3 px-4 text-secondary text-[11px]">
                          {Math.round((item.file_size_bytes / 1024) * 10) / 10} KB
                        </td>
                        <td className="py-3 px-4 text-right">
                          <button
                            onClick={() => handleDownload(item)}
                            disabled={downloadingId === item.id}
                            className="px-2.5 py-1 bg-white border border-border hover:bg-slate-50 text-dark rounded-md text-[11px] font-medium inline-flex items-center gap-1 shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
                            title="Download Report File"
                          >
                            <Download className="w-3 h-3 text-secondary" />
                            <span>Download</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-border flex items-center justify-between">
          <span className="text-[11px] text-secondary">
            Showing {historyItems.length} recent report generation records.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-white border border-border rounded-lg text-xs font-medium text-dark hover:bg-slate-100 cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
