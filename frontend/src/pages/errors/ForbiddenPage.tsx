import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, LayoutDashboard } from 'lucide-react';

export const ForbiddenPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-center">
      <div className="w-14 h-14 rounded-2xl bg-rose-50 text-danger flex items-center justify-center mb-4 shadow-sm border border-rose-200">
        <ShieldAlert className="w-8 h-8" />
      </div>

      <span className="text-4xl font-extrabold text-danger font-mono tracking-tight">403</span>
      <h1 className="text-xl font-bold text-dark mt-2">Access Denied &bull; Insufficient Permissions</h1>
      <p className="text-xs text-secondary mt-1 max-w-sm">
        Your current role does not have authorization to view this organization resource or perform this audit action.
      </p>

      <div className="flex items-center gap-3 mt-6">
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 bg-white border border-border rounded-lg text-xs font-semibold text-dark hover:bg-slate-50 flex items-center gap-1.5 shadow-sm transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Go Back</span>
        </button>

        <Link
          to="/"
          className="px-4 py-2 bg-primary text-white rounded-lg text-xs font-semibold hover:bg-primary-hover flex items-center gap-1.5 shadow-sm transition-colors"
        >
          <LayoutDashboard className="w-3.5 h-3.5" />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    </div>
  );
};
