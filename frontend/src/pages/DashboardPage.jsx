import React, { useState, useEffect } from 'react';
import './DashboardPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

function DashboardPage() {
  const [activities, setActivities] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const wsUrl = import.meta.env.VITE_API_BASE_URL?.replace('http', 'ws') || 'ws://localhost:8000';
    const ws = new WebSocket(`${wsUrl}/api/ws/admin/verify-feed`);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected to live activity feed');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.event !== 'clock_event' || !data.match || !data.action) {
          return;
        }

        const newActivity = {
          id: Date.now() + Math.random(),
          timestamp: new Date().toISOString(),
          employeeName: data.match.name || 'Unknown',
          employeeEmail: data.match.email,
          employeeId: data.match.employee_id,
          action: data.action,
          similarity: data.similarity,
          verified: data.verified
        };

        setActivities(prev => [newActivity, ...prev].slice(0, 50));
      } catch (error) {
        console.error('Error parsing websocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    return () => {
      ws.close();
    };
  }, []);

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  const getActivityIcon = (action) => {
    if (action === 'IN') return '🟢';
    if (action === 'OUT') return '🔴';
    return '📋';
  };

  const getActivityLabel = (action) => {
    if (action === 'IN') return 'Clocked In';
    if (action === 'OUT') return 'Clocked Out';
    return 'Activity';
  };

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

            <div className="live-activity-feed">
              <div className="activity-feed-header">
                <h2 className="activity-feed-title">Live Activity Feed</h2>
                <span 
                  className="activity-status-indicator" 
                  style={{ color: isConnected ? '#10b981' : '#6b7280' }}
                >
                  ●
                </span>
              </div>
              <div className="activity-feed-content">
                {activities.length === 0 ? (
                  <div className="activity-empty-state">
                    <div className="activity-empty-icon">📡</div>
                    <p className="activity-empty-text">
                      {isConnected 
                        ? 'Waiting for live scanner activity...' 
                        : 'Connecting to live feed...'}
                    </p>
                  </div>
                ) : (
                  <div className="activity-list">
                    {activities.map((activity) => (
                      <div key={activity.id} className="activity-item">
                        <div className="activity-icon">
                          {getActivityIcon(activity.action)}
                        </div>
                        <div className="activity-details">
                          <div className="activity-main">
                            <span className="activity-name">
                              {activity.employeeName}
                            </span>
                            <span className="activity-action">
                              {getActivityLabel(activity.action)}
                            </span>
                          </div>
                          {activity.verified !== undefined && (
                            <div className="activity-meta">
                              {activity.verified ? '✓ Verified' : '⚠ Unverified'}
                              {activity.similarity !== undefined && 
                                ` • ${Math.round(activity.similarity * 100)}% match`
                              }
                            </div>
                          )}
                        </div>
                        <div className="activity-time">
                          {formatTimestamp(activity.timestamp)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
