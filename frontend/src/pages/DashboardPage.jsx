/**
 * DashboardPage - Basic Dashboard Shell (Scrum 11)
 * 
 * Features:
 * - Navbar on top
 * - Sidebar navigation on left
 * - Content area with card container
 * - Welcome message and placeholder text
 */

import React from 'react';
import './DashboardPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

function DashboardPage() {
  return (
    <div className="dashboard-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <h1>Welcome to ClockGuard Admin Panel.</h1>
            <p>Content Area (Dashboard features coming in Sprint 2)</p>
          </div>
        </main>
      </div>
    </div>
  );
}

export default DashboardPage;
