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
          <div className="dashboard-container">
            <div className="dashboard-header">
              <h1 className="dashboard-title">Live Metrics</h1>
              <p className="dashboard-subtitle">
                Monitor employee attendance and system activity in real-time
              </p>
            </div>

            <div className="stats-row">
              <div className="stat-card">
                <div className="stat-value">0</div>
                <div className="stat-label">Clocked In</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">0</div>
                <div className="stat-label">Clocked Out</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">0</div>
                <div className="stat-label">Failed Logins</div>
              </div>
            </div>

            <div className="kanban-board">
              <div className="kanban-column clocked-in-column">
                <div className="column-header">
                  <div className="column-icon clocked-in-icon">●</div>
                  <h2 className="column-title">Clocked In</h2>
                  <span className="column-count">0</span>
                </div>
                <div className="column-content">
                  <div className="empty-state-card">
                    <div className="empty-icon">👥</div>
                    <p className="empty-text">No employees currently clocked in</p>
                  </div>
                </div>
              </div>

              <div className="kanban-column clocked-out-column">
                <div className="column-header">
                  <div className="column-icon clocked-out-icon">●</div>
                  <h2 className="column-title">Clocked Out</h2>
                  <span className="column-count">0</span>
                </div>
                <div className="column-content">
                  <div className="empty-state-card">
                    <div className="empty-icon">🏠</div>
                    <p className="empty-text">No employees currently clocked out</p>
                  </div>
                </div>
              </div>

              <div className="kanban-column security-column">
                <div className="column-header">
                  <div className="column-icon security-icon">●</div>
                  <h2 className="column-title">Security</h2>
                  <span className="column-count">-</span>
                </div>
                <div className="column-content">
                  <div className="info-card">
                    <div className="info-icon">🔒</div>
                    <h3 className="info-title">Failed Login Tracking</h3>
                    <p className="info-description">
                      Login attempt monitoring is not currently enabled
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default DashboardPage;
