/**
 * DashboardPage - With Navbar (Scrum 9)
 * 
 * Scrum 11 will implement the full dashboard shell with:
 * - Sidebar navigation
 * - Main content area
 * - Welcome/overview content
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
          <h1>Welcome to ClockGuard Admin Panel</h1>
          <p>Dashboard layout and navigation coming in Scrum 11</p>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
