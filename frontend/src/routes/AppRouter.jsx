/**
 * AppRouter - Routing Configuration
 * 
 * Routes:
 * - / -> redirects to /login
 * - /login -> LoginPage
 * - /dashboard -> DashboardPage
 * 
 * Authentication logic and route guards will be added in future sprints.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import DashboardPage from '../pages/DashboardPage';

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default redirect to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        
        {/* Login page */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Dashboard page */}
        <Route path="/dashboard" element={<DashboardPage />} />
        
        {/* Catch-all redirect to login */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
