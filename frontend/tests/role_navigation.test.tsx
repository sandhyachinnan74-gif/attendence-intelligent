import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { TopNavbar } from '../src/components/layout/TopNavbar';
import { Sidebar } from '../src/components/layout/Sidebar';
import * as AuthContext from '../src/context/AuthContext';

describe('Role Navigation & Clean Commercial UI', () => {
  const mockAuth = (role: 'admin' | 'hr_manager' | 'employee', name: string) => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      user: {
        id: 'user-123',
        email: `${role}@attendai.com`,
        role,
        organization_id: 'org-123',
        first_name: name.split(' ')[0],
        last_name: name.split(' ')[1] || 'User',
      },
      token: 'fake-token',
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      isLoading: false,
    });
  };

  it('TopNavbar renders clean enterprise controls without internal engine badges', () => {
    mockAuth('employee', 'Sarah Connor');
    render(
      <BrowserRouter>
        <TopNavbar collapsed={false} />
      </BrowserRouter>
    );

    // Global search and notification center controls must exist
    expect(screen.getByPlaceholderText(/search my attendance, shifts, leave, policies/i)).toBeInTheDocument();
    
    // Internal indicators must NOT exist
    expect(screen.queryByText(/Engine Active/i)).toBeNull();
    expect(screen.queryByText(/Role-scoped authorization/i)).toBeNull();
    expect(screen.queryByText(/Record privacy guaranteed/i)).toBeNull();
  });

  it('Sidebar for Employee renders employee-specific navigation only', () => {
    mockAuth('employee', 'Sarah Connor');
    render(
      <BrowserRouter>
        <Sidebar collapsed={false} onToggle={() => {}} />
      </BrowserRouter>
    );

    // Employee items
    expect(screen.getByText('My Dashboard')).toBeInTheDocument();
    expect(screen.getByText('My Attendance')).toBeInTheDocument();
    expect(screen.getByText('My Shifts')).toBeInTheDocument();
    expect(screen.getByText('My Leave')).toBeInTheDocument();
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();

    // Admin/HR only items must NOT be present
    expect(screen.queryByText('System Diagnostics')).toBeNull();
    expect(screen.queryByText('Audit Logs')).toBeNull();
    expect(screen.queryByText('Anomaly Detection')).toBeNull();
    expect(screen.queryByText('Analytics & Reports')).toBeNull();

    // Security indicator panels must NOT be present
    expect(screen.queryByText(/EMPLOYEE Scope/i)).toBeNull();
    expect(screen.queryByText(/Role-scoped authorization enforced/i)).toBeNull();
  });

  it('Sidebar for HR Manager renders HR navigation and excludes Admin diagnostics', () => {
    mockAuth('hr_manager', 'Michael Scott');
    render(
      <BrowserRouter>
        <Sidebar collapsed={false} onToggle={() => {}} />
      </BrowserRouter>
    );

    // HR items
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Employees')).toBeInTheDocument();
    expect(screen.getByText('Shifts & Scheduling')).toBeInTheDocument();
    expect(screen.getByText('Leave Management')).toBeInTheDocument();
    expect(screen.getByText('Anomaly Detection')).toBeInTheDocument();

    // Admin-only items must NOT be present
    expect(screen.queryByText('System Diagnostics')).toBeNull();
    expect(screen.queryByText('Audit Logs')).toBeNull();
    expect(screen.queryByText('HR Scope')).toBeNull();
  });

  it('Sidebar for Admin renders complete enterprise management navigation', () => {
    mockAuth('admin', 'Admin User');
    render(
      <BrowserRouter>
        <Sidebar collapsed={false} onToggle={() => {}} />
      </BrowserRouter>
    );

    // Admin items
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Employees')).toBeInTheDocument();
    expect(screen.getByText('Departments')).toBeInTheDocument();
    expect(screen.getByText('System Diagnostics')).toBeInTheDocument();
    expect(screen.getByText('Audit Logs')).toBeInTheDocument();
    
    // Internal indicator badge must NOT be present
    expect(screen.queryByText(/ADMIN Scope/i)).toBeNull();
  });
});
