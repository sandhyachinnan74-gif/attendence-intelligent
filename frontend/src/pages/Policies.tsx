import React, { useEffect, useState } from 'react';
import { Upload, FileText, Search, Trash2, BookOpen, CheckCircle, ExternalLink, X, Download, FileDown, Eye } from 'lucide-react';
import { api } from '../services/api';
import { Policy, PolicyChunk } from '../types';
import { useAuth } from '../context/AuthContext';
import { downloadFile } from '../utils/download';

export const Policies: React.FC = () => {
  const { user } = useAuth();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);

  // Search across policies
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PolicyChunk[]>([]);
  const [searching, setSearching] = useState(false);

  // Document Reader state
  const [selectedPolicy, setSelectedPolicy] = useState<any | null>(null);
  const [readingPolicy, setReadingPolicy] = useState(false);
  const [docSearch, setDocSearch] = useState('');

  // Upload modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadCategory, setUploadCategory] = useState('Attendance & Leave');
  const [uploading, setUploading] = useState(false);

  const fetchPolicies = async () => {
    setLoading(true);
    try {
      const res = await api.get('/policies');
      setPolicies(res.data);
    } catch (e) {
      console.error('Failed to load policies:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPolicies();
  }, []);

  const handleOpenDocument = async (id: string) => {
    setReadingPolicy(true);
    setDocSearch('');
    try {
      const res = await api.get(`/policies/${id}`);
      setSelectedPolicy(res.data);
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to load document content');
    } finally {
      setReadingPolicy(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await api.get('/policies/search', { params: { query: searchQuery } });
      setSearchResults(res.data);
    } catch (e) {
      console.error('Failed to execute policy search:', e);
    } finally {
      setSearching(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !uploadTitle) return;

    setUploading(true);
    const form = new FormData();
    form.append('file', uploadFile);
    form.append('title', uploadTitle);
    form.append('category', uploadCategory);

    try {
      await api.post('/policies/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadTitle('');
      fetchPolicies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDeletePolicy = async (id: string) => {
    if (!confirm('Are you sure you want to delete this policy and all its indexed chunks?')) return;
    try {
      await api.delete(`/policies/${id}`);
      if (selectedPolicy?.id === id) {
        setSelectedPolicy(null);
      }
      fetchPolicies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete policy');
    }
  };

  const canUpload = user?.role === 'admin' || user?.role === 'hr_manager';

  const filteredChunks = selectedPolicy?.chunks?.filter((c: any) => {
    if (!docSearch.trim()) return true;
    const q = docSearch.toLowerCase();
    return (
      (c.content && c.content.toLowerCase().includes(q)) ||
      (c.section && c.section.toLowerCase().includes(q))
    );
  }) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Policies & Guidelines</h1>
          <p className="text-xs text-secondary mt-0.5">
            Full-text policy repository with PyMuPDF/python-docx indexing, search citations, and document reading.
          </p>
        </div>
        {canUpload && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="px-3.5 py-1.5 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        )}
      </div>

      {/* Interactive Policy Search Bar */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-4">
        <div>
          <h2 className="text-sm font-bold text-dark">Policy Search & Citation Lookup</h2>
          <p className="text-xs text-secondary mt-0.5">
            Search across company policies, attendance guidelines, and leave regulations.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. grace period, overtime calculation, sick leave medical certificate..."
              className="w-full pl-9 pr-4 py-2 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:outline-none focus:ring-1 focus:ring-primary focus:bg-white"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !searchQuery.trim()}
            className="px-4 py-2 bg-primary text-white text-xs font-semibold rounded-lg hover:bg-primary-hover shadow-sm disabled:opacity-50"
          >
            {searching ? 'Searching...' : 'Search Policies'}
          </button>
        </form>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="pt-3 border-t border-border space-y-3">
            <span className="text-xs font-bold text-dark block">
              Search Results ({searchResults.length} relevant sections found)
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {searchResults.map((chunk) => (
                <div key={chunk.id} className="p-3.5 rounded-lg bg-slate-50 border border-border space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-primary font-semibold">
                    <span>{chunk.title}</span>
                    <span className="text-[10px] text-secondary font-mono">
                      Page {chunk.page_number} ({chunk.section})
                    </span>
                  </div>
                  <p className="text-dark leading-relaxed font-normal">{chunk.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Uploaded Documents List */}
      <div className="bg-card border border-border rounded-xl shadow-card overflow-hidden">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-dark">Indexed Policy Documents</h2>
            <p className="text-xs text-secondary mt-0.5">Click any document to read its full contents or download a copy.</p>
          </div>
          <span className="text-xs text-secondary font-medium">{policies.length} Documents</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Document Title</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">File Size</th>
                <th className="py-3 px-4">Indexed Pages</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border font-medium">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-secondary">
                    Loading policies...
                  </td>
                </tr>
              ) : policies.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-secondary">
                    No documents uploaded yet.
                  </td>
                </tr>
              ) : (
                policies.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4">
                      <button
                        onClick={() => handleOpenDocument(p.id)}
                        className="flex items-center gap-2.5 text-left group"
                        title="Click to read document"
                      >
                        <FileText className="w-4 h-4 text-primary flex-shrink-0 group-hover:scale-110 transition-transform" />
                        <span className="font-semibold text-dark group-hover:text-primary transition-colors underline decoration-transparent group-hover:decoration-primary">
                          {p.title}
                        </span>
                      </button>
                    </td>
                    <td className="py-3 px-4 text-secondary">{p.category}</td>
                    <td className="py-3 px-4 font-mono text-secondary">{Math.round(p.file_size / 1024)} KB</td>
                    <td className="py-3 px-4 font-mono text-dark">{p.chunk_count} pages/chunks</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-success border border-emerald-200 capitalize">
                        <CheckCircle className="w-3 h-3" />
                        <span>{p.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleOpenDocument(p.id)}
                          className="px-2.5 py-1 bg-white border border-border text-dark rounded-md text-xs font-medium hover:bg-slate-50 flex items-center gap-1 shadow-xs transition-colors"
                          title="Read Document Content"
                        >
                          <BookOpen className="w-3.5 h-3.5 text-primary" />
                          <span>Read</span>
                        </button>
                        <button
                          onClick={() => downloadFile(`/policies/${p.id}/download`, `${p.title}.pdf`)}
                          className="p-1 rounded text-secondary hover:text-dark hover:bg-slate-100 transition-colors"
                          title="Download Document"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </button>
                        {canUpload && (
                          <button
                            onClick={() => handleDeletePolicy(p.id)}
                            className="p-1 rounded text-secondary hover:text-danger hover:bg-rose-50 transition-colors"
                            title="Delete Policy"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Document Reader Modal */}
      {selectedPolicy && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-border bg-slate-50/75 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-dark">{selectedPolicy.title}</h3>
                  <div className="flex items-center gap-2 text-xs text-secondary mt-0.5">
                    <span className="px-2 py-0.2 bg-white border border-border rounded text-[10px] font-semibold">
                      {selectedPolicy.category}
                    </span>
                    <span>&bull;</span>
                    <span>{selectedPolicy.chunks?.length || 0} indexed sections</span>
                    <span>&bull;</span>
                    <span>{Math.round((selectedPolicy.file_size || 0) / 1024)} KB</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => downloadFile(`/policies/${selectedPolicy.id}/download`, `${selectedPolicy.title}.pdf`)}
                  className="px-3 py-1.5 bg-white border border-border text-dark rounded-lg text-xs font-semibold hover:bg-slate-50 flex items-center gap-1.5 shadow-xs"
                >
                  <Download className="w-3.5 h-3.5 text-secondary" />
                  <span>Download File</span>
                </button>
                <button
                  onClick={() => setSelectedPolicy(null)}
                  className="p-1.5 rounded-lg text-secondary hover:text-dark hover:bg-slate-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Document Content Search Filter */}
            <div className="px-6 py-3 border-b border-border/80 bg-white flex items-center gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-secondary" />
                <input
                  type="text"
                  placeholder="Filter sections within this document..."
                  value={docSearch}
                  onChange={(e) => setDocSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <span className="text-xs text-secondary flex-shrink-0">
                Showing {filteredChunks.length} of {selectedPolicy.chunks?.length || 0} sections
              </span>
            </div>

            {/* Reader Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/40">
              {filteredChunks.length === 0 ? (
                <div className="text-center py-12 text-secondary text-xs">
                  No sections match "{docSearch}".
                </div>
              ) : (
                filteredChunks.map((chunk: any, idx: number) => (
                  <div
                    key={chunk.id || idx}
                    className="bg-white border border-border rounded-xl p-5 shadow-xs space-y-2.5"
                  >
                    <div className="flex items-center justify-between pb-2 border-b border-border/60">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-primary/10 text-primary font-mono font-bold text-[10px] rounded">
                          Page {chunk.page_number}
                        </span>
                        <span className="font-bold text-xs text-dark">
                          {chunk.section || `Section ${idx + 1}`}
                        </span>
                      </div>
                      <span className="text-[10px] text-secondary font-mono">
                        {chunk.token_count} tokens
                      </span>
                    </div>

                    <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap font-sans">
                      {chunk.content}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-border bg-slate-50 flex items-center justify-between text-xs text-secondary">
              <span>AttendAI Document Parser &bull; PyMuPDF / python-docx</span>
              <button
                onClick={() => setSelectedPolicy(null)}
                className="px-4 py-1.5 bg-white border border-border rounded-lg font-medium text-dark hover:bg-slate-100"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-border rounded-xl shadow-xl w-full max-w-md overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-dark">Upload Policy Document</h3>
              <button onClick={() => setShowUploadModal(false)} className="text-secondary hover:text-dark">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUpload} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-dark mb-1">Document Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Employee Handbook 2026"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Category</label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                >
                  <option value="Attendance & Punctuality">Attendance & Punctuality</option>
                  <option value="Leave Management">Leave Management</option>
                  <option value="Code of Conduct">Code of Conduct</option>
                  <option value="General HR">General HR</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-dark mb-1">Select File (PDF, DOCX, TXT)</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full px-3 py-2 text-xs bg-slate-50 border border-border rounded-lg text-dark focus:bg-white"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-border">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 border border-border rounded-lg text-xs font-medium text-secondary hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover shadow-sm disabled:opacity-50"
                >
                  {uploading ? 'Extracting & Indexing...' : 'Upload & Process'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
