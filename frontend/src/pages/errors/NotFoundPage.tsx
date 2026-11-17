import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Clock, ArrowLeft, LayoutDashboard, Search } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-6 text-center">
      <div className="w-14 h-14 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-4 shadow-sm">
        <Clock className="w-8 h-8" />
      </div>

      <span className="text-4xl font-extrabold text-primary font-mono tracking-tight">404</span>
      <h1 className="text-xl font-bold text-dark mt-2">Workforce Resource Not Found</h1>
      <p className="text-xs text-secondary mt-1 max-w-sm">
        The requested workforce page, employee profile, or audit URL does not exist or has been relocated.
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
          <span>Go to Dashboard</span>
        </Link>
      </div>
    </div>
  );
};
