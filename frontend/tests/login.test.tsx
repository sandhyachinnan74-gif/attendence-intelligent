import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Login } from '../src/pages/Login';
import { AuthProvider } from '../src/context/AuthContext';

describe('Login Component', () => {
  it('renders AttendAI branding and input fields', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText('AttendAI')).toBeInTheDocument();
    expect(screen.getByText('Intelligent Workforce. Smarter Decisions.')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('name@company.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
  });

  it('renders quick demo account buttons', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Admin')).toBeInTheDocument();
    expect(screen.getByText('HR Mgr')).toBeInTheDocument();
    expect(screen.getByText('Employee')).toBeInTheDocument();
  });

  it('fills inputs when demo account button is clicked', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthProvider>
    );

    const adminBtn = screen.getByText('Admin');
    fireEvent.click(adminBtn);

    const emailInput = screen.getByPlaceholderText('name@company.com') as HTMLInputElement;
    expect(emailInput.value).toBe('admin@attendai.com');
  });
});
