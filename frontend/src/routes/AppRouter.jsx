/**
 * AppRouter - Routing Configuration
 * 
 * Routes:
 * - / -> redirects to /login
 * - /login -> LoginPage
 * - /dashboard -> DashboardPage
 * - /employees -> EmployeesPage
 * - /settings -> SettingsPage
 * 
 * Authentication logic and route guards will be added in future sprints.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import DashboardPage from '../pages/DashboardPage';
import EmployeesPage from '../pages/EmployeesPage';
import SettingsPage from '../pages/SettingsPage';

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default redirect to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* Login page */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Dashboard pages */}
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        
        {/* Catch-all redirect to login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
