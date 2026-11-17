import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { AppLayout } from '../components/layout/AppLayout';
import { Login } from '../pages/Login';
import { Dashboard } from '../pages/Dashboard';
import { Employees } from '../pages/Employees';
import { Attendance } from '../pages/Attendance';
import { Shifts } from '../pages/Shifts';
import { Leave } from '../pages/Leave';
import { Anomalies } from '../pages/Anomalies';
import { AIAssistant } from '../pages/AIAssistant';
import { Policies } from '../pages/Policies';
import { Analytics } from '../pages/Analytics';
import { Settings } from '../pages/Settings';
import { HelpSupport } from '../pages/HelpSupport';
import { NotFoundPage } from '../pages/errors/NotFoundPage';
import { ForbiddenPage } from '../pages/errors/ForbiddenPage';
import { ServerErrorPage } from '../pages/errors/ServerErrorPage';

const RoleGuard: React.FC<{ allowedRoles: string[]; children: React.ReactNode }> = ({ allowedRoles, children }) => {
  const { user } = useAuth();
  if (user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/403" replace />;
  }
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          {/* Protected Application Routes */}
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route
              path="employees"
              element={
                <RoleGuard allowedRoles={['admin', 'hr_manager']}>
                  <Employees />
                </RoleGuard>
              }
            />
            <Route path="attendance" element={<Attendance />} />
            <Route
              path="shifts"
              element={
                <RoleGuard allowedRoles={['admin', 'hr_manager']}>
                  <Shifts />
                </RoleGuard>
              }
            />
            <Route path="leave" element={<Leave />} />
            <Route
              path="anomalies"
              element={
                <RoleGuard allowedRoles={['admin', 'hr_manager']}>
                  <Anomalies />
                </RoleGuard>
              }
            />
            <Route path="ai" element={<AIAssistant />} />
            <Route path="policies" element={<Policies />} />
            <Route
              path="analytics"
              element={
                <RoleGuard allowedRoles={['admin', 'hr_manager']}>
                  <Analytics />
                </RoleGuard>
              }
            />
            <Route path="settings" element={<Settings />} />
            <Route path="help" element={<HelpSupport />} />
            <Route path="403" element={<ForbiddenPage />} />
            <Route path="500" element={<ServerErrorPage />} />
          </Route>

          {/* 404 Route */}
          <Route path="/404" element={<NotFoundPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
