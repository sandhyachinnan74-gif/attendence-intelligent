import React from 'react';
import { HelpCircle, Book, Shield, Bot, Clock, MessageSquare } from 'lucide-react';
import { Link } from 'react-router-dom';

export const HelpSupport: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl">
      <div className="pb-4 border-b border-border">
        <h1 className="text-xl font-bold text-dark tracking-tight">Help & Knowledge Base</h1>
        <p className="text-xs text-secondary mt-0.5">
          Guides, role permissions matrix, and workforce policy references.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-2">
          <div className="flex items-center gap-2 text-primary font-bold text-sm">
            <Clock className="w-4 h-4" />
            <span>Attendance & Clock-In</span>
          </div>
          <p className="text-xs text-secondary leading-relaxed">
            Punches are recorded against server UTC timestamps. The standard grace period is 15 minutes. Employees arriving past
            the grace period will have their record marked as Late Arrival.
          </p>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-2">
          <div className="flex items-center gap-2 text-purple-600 font-bold text-sm">
            <Shield className="w-4 h-4" />
            <span>Role Permissions & RBAC</span>
          </div>
          <p className="text-xs text-secondary leading-relaxed">
            AttendAI enforces strict record-level scoping. Employees can only access their own attendance records.
            HR managers manage department workforce records. Administrators have organization-level authority.
          </p>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-2">
          <div className="flex items-center gap-2 text-emerald-600 font-bold text-sm">
            <Bot className="w-4 h-4" />
            <span>Workforce AI Intelligence</span>
          </div>
          <p className="text-xs text-secondary leading-relaxed">
            Our conversational assistant connects exclusively to registered backend tools. Responses cite real
            PostgreSQL attendance metrics or indexed company policy pages.
          </p>
          <Link to="/ai" className="text-xs font-semibold text-primary hover:underline block pt-1">
            Open AI Assistant &rarr;
          </Link>
        </div>

        <div className="bg-card border border-border rounded-xl p-5 shadow-card space-y-2">
          <div className="flex items-center gap-2 text-amber-600 font-bold text-sm">
            <Book className="w-4 h-4" />
            <span>HR Policies Repository</span>
          </div>
          <p className="text-xs text-secondary leading-relaxed">
            All company policies, code of conduct, and leave guidelines are indexed for full-text search.
          </p>
          <Link to="/policies" className="text-xs font-semibold text-primary hover:underline block pt-1">
            Browse Documents &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
};
