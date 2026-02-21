/**
 * DashboardPage - Basic Dashboard Shell (Scrum 11)
 * 
 * Features:
 * - Navbar on top
 * - Content area below
 * - Welcome message
 */

import React from 'react';
import './DashboardPage.css';
import Navbar from '../components/Navbar';

function DashboardPage() {
  return (
    <div className="dashboard-page">
      <Navbar />
      <div className="dashboard-content">
        <div className="dashboard-placeholder">
          <h1>Welcome to ClockGuard Admin Panel.</h1>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
