import React, { useEffect, useState } from 'react';
import { Upload, FileText, Search, Trash2, BookOpen, CheckCircle, ExternalLink, X } from 'lucide-react';
import { api } from '../services/api';
import { Policy, PolicyChunk } from '../types';
import { useAuth } from '../context/AuthContext';

export const Policies: React.FC = () => {
  const { user } = useAuth();
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);

  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<PolicyChunk[]>([]);
  const [searching, setSearching] = useState(false);

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
      fetchPolicies();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete policy');
    }
  };

  const canUpload = user?.role === 'admin' || user?.role === 'hr_manager';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-dark tracking-tight">Policies & Guidelines</h1>
          <p className="text-xs text-secondary mt-0.5">
            Full-text policy repository with PyMuPDF/python-docx indexing and page citations.
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
        <div className="px-5 py-3.5 border-b border-border">
          <h2 className="text-sm font-bold text-dark">Indexed Policy Documents</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-slate-50/75 text-secondary uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Document Title</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">File Size</th>
                <th className="py-3 px-4">Chunks</th>
                <th className="py-3 px-4">Status</th>
                {canUpload && <th className="py-3 px-4 text-right">Action</th>}
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
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-4 h-4 text-primary flex-shrink-0" />
                        <span className="font-semibold text-dark">{p.title}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-secondary">{p.category}</td>
                    <td className="py-3 px-4 font-mono text-secondary">{Math.round(p.file_size / 1024)} KB</td>
                    <td className="py-3 px-4 font-mono text-dark">{p.chunk_count} chunks</td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-success border border-emerald-200 capitalize">
                        <CheckCircle className="w-3 h-3" />
                        <span>{p.status}</span>
                      </span>
                    </td>
                    {canUpload && (
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleDeletePolicy(p.id)}
                          className="p-1 rounded text-secondary hover:text-danger transition-colors"
                          title="Delete Policy"
                        >
                          <Trash2 className="w-4 h-4" />
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
