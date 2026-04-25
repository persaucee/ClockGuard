import React, { useState, useEffect, useMemo } from 'react';
import './DashboardPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { api } from '../services/apiClient';

function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getEmployeeId(emp) {
  return emp?.employee_id || emp?.id || null;
}

function getEmployeeName(emp) {
  return emp?.name || emp?.employee_name || 'Unknown';
}

const TWENTY_FOUR_HOURS_MS = 24 * 60 * 60 * 1000;

function DashboardPage() {
  const [clockedInList, setClockedInList] = useState([]);
  const [recentlyClockedOutList, setRecentlyClockedOutList] = useState([]);
  const [inactiveList, setInactiveList] = useState([]);
  const [activities, setActivities] = useState([]);
  const [expandedFeedEmployees, setExpandedFeedEmployees] = useState(new Set());
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initial data fetch
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch 200 logs so we have enough coverage for the 24h "recently clocked out" window
        const [status, recentLogs] = await Promise.all([
          api.attendance.getStatus(),
          api.attendance.getRecentLogs(200),
        ]);

        setClockedInList(status.clocked_in || []);
        setInactiveList(status.inactive || []);

        // Derive "recently clocked out": employees whose most recent log is OUT within 24h
        // and who are not already in clocked_in (backend is authoritative for active state)
        const clockedInIds = new Set(
          (status.clocked_in || []).map((e) => getEmployeeId(e))
        );
        const cutoff = Date.now() - TWENTY_FOUR_HOURS_MS;

        const latestLogPerEmployee = {};
        recentLogs.forEach((log) => {
          const empId = log.employee_id;
          if (!empId) return;
          const existing = latestLogPerEmployee[empId];
          if (!existing || new Date(log.timestamp) > new Date(existing.timestamp)) {
            latestLogPerEmployee[empId] = log;
          }
        });

        const derivedRecentlyClockedOut = Object.values(latestLogPerEmployee)
          .filter(
            (log) =>
              log.action === 'OUT' &&
              new Date(log.timestamp).getTime() >= cutoff &&
              !clockedInIds.has(log.employee_id)
          )
          .map((log) => ({
            name: log.employee_name || 'Unknown',
            employee_id: log.employee_id,
          }));

        setRecentlyClockedOutList(derivedRecentlyClockedOut);

        // Only show the 50 most recent events in the activity feed
        const initialActivities = recentLogs.slice(0, 50).map((log, i) => ({
          id: log.id || `${log.employee_id}-${log.timestamp}-${i}`,
          timestamp: log.timestamp,
          employeeName: log.employee_name || 'Unknown',
          employeeId: log.employee_id,
          action: log.action,
          verified: log.verified,
          similarity: log.similarity,
        }));
        setActivities(initialActivities);
      } catch (err) {
        setError(err.message || 'Failed to load dashboard data');
        console.error('Dashboard fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  // WebSocket connection for live updates
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
          verified: data.verified,
        };

        setActivities(prev => [newActivity, ...prev].slice(0, 50));

        const employeeEntry = {
          name: data.match.name || 'Unknown',
          employee_id: data.match.employee_id,
          email: data.match.email,
        };

        if (data.action === 'IN') {
          setClockedInList(prev => {
            const alreadyIn = prev.some(e => getEmployeeId(e) === data.match.employee_id);
            if (alreadyIn) return prev;
            return [employeeEntry, ...prev];
          });
          // Clear from both OUT-related lists when someone clocks back in
          setRecentlyClockedOutList(prev =>
            prev.filter(e => getEmployeeId(e) !== data.match.employee_id)
          );
          setInactiveList(prev =>
            prev.filter(e => getEmployeeId(e) !== data.match.employee_id)
          );
        } else if (data.action === 'OUT') {
          setRecentlyClockedOutList(prev => {
            const alreadyOut = prev.some(e => getEmployeeId(e) === data.match.employee_id);
            if (alreadyOut) return prev;
            return [employeeEntry, ...prev];
          });
          setClockedInList(prev =>
            prev.filter(e => getEmployeeId(e) !== data.match.employee_id)
          );
        }
      } catch (err) {
        console.error('Error parsing websocket message:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
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
      second: '2-digit',
    });
  };

  const formatDate = (timestamp) =>
    new Date(timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  // Group activities by employee, sorted by most recent event first
  const groupedActivities = useMemo(() => {
    const groups = {};
    activities.forEach((activity) => {
      const key = activity.employeeId || activity.employeeName;
      if (!groups[key]) {
        groups[key] = {
          key,
          employeeName: activity.employeeName,
          employeeId: activity.employeeId,
          events: [],
        };
      }
      groups[key].events.push(activity);
    });

    return Object.values(groups)
      .map((g) => {
        g.events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        g.latestEvent = g.events[0];
        return g;
      })
      .sort((a, b) => new Date(b.latestEvent.timestamp) - new Date(a.latestEvent.timestamp));
  }, [activities]);

  const toggleFeedEmployee = (key) => {
    setExpandedFeedEmployees((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const renderEmployeeCard = (emp) => {
    const id = getEmployeeId(emp);
    const name = getEmployeeName(emp);
    return (
      <div key={id || name} className="kanban-employee-card">
        <div className="kanban-employee-avatar">{getInitials(name)}</div>
        <div className="kanban-employee-info">
          <span className="kanban-employee-name">{name}</span>
          {id && <span className="kanban-employee-id">ID: {id}</span>}
        </div>
      </div>
    );
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

            {error && (
              <div className="dashboard-error">
                <span>⚠</span> {error}
              </div>
            )}

            <div className="stats-row">
              <div className="stat-card">
                <div className="stat-value">
                  {loading ? '—' : clockedInList.length}
                </div>
                <div className="stat-label">Clocked In</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">
                  {loading ? '—' : inactiveList.length}
                </div>
                <div className="stat-label">Inactive</div>
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
                {loading ? (
                  <div className="activity-empty-state">
                    <div className="activity-empty-icon">⏳</div>
                    <p className="activity-empty-text">Loading activity feed...</p>
                  </div>
                ) : groupedActivities.length === 0 ? (
                  <div className="activity-empty-state">
                    <div className="activity-empty-icon">📡</div>
                    <p className="activity-empty-text">
                      {isConnected
                        ? 'Waiting for live scanner activity...'
                        : 'Connecting to live feed...'}
                    </p>
                  </div>
                ) : (
                  <div className="feed-employee-list">
                    {groupedActivities.map((group) => {
                      const isExpanded = expandedFeedEmployees.has(group.key);
                      const latestAction = group.latestEvent.action.toLowerCase();
                      return (
                        <div
                          key={group.key}
                          className={`feed-employee-card${isExpanded ? ' feed-employee-card--open' : ''}`}
                        >
                          <button
                            className="feed-employee-header"
                            onClick={() => toggleFeedEmployee(group.key)}
                            aria-expanded={isExpanded}
                          >
                            <div className={`feed-avatar feed-avatar--${latestAction}`}>
                              {getInitials(group.employeeName)}
                            </div>
                            <div className="feed-employee-info">
                              <span className="feed-employee-name">{group.employeeName}</span>
                              <span className="feed-employee-meta">
                                {group.events.length} {group.events.length === 1 ? 'event' : 'events'}
                              </span>
                            </div>
                            <div className="feed-employee-right">
                              <span className={`feed-action-badge feed-action--${latestAction}`}>
                                {group.latestEvent.action === 'IN' ? 'Clocked In' : 'Clocked Out'}
                              </span>
                              <span className="feed-latest-time">
                                {formatTimestamp(group.latestEvent.timestamp)}
                              </span>
                              <span className={`feed-chevron${isExpanded ? ' feed-chevron--open' : ''}`}>
                                ›
                              </span>
                            </div>
                          </button>

                          {isExpanded && (
                            <div className="feed-timeline">
                              {group.events.map((event, index) => (
                                <div key={event.id} className="feed-timeline-item">
                                  <div className="feed-timeline-rail">
                                    <div className={`feed-timeline-dot feed-timeline-dot--${event.action.toLowerCase()}`} />
                                    {index < group.events.length - 1 && (
                                      <div className="feed-timeline-line" />
                                    )}
                                  </div>
                                  <div className="feed-timeline-body">
                                    <span className={`feed-action-badge feed-action--${event.action.toLowerCase()}`}>
                                      {event.action}
                                    </span>
                                    <span className="feed-timeline-date">
                                      {formatDate(event.timestamp)}
                                    </span>
                                    <span className="feed-latest-time">
                                      {formatTimestamp(event.timestamp)}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            <div className="kanban-board">
              <div className="kanban-column clocked-in-column">
                <div className="column-header">
                  <div className="column-icon clocked-in-icon">●</div>
                  <h2 className="column-title">Clocked In</h2>
                  <span className="column-count">
                    {loading ? '—' : clockedInList.length}
                  </span>
                </div>
                <div className="column-content">
                  {loading ? (
                    <div className="empty-state-card">
                      <p className="empty-text">Loading...</p>
                    </div>
                  ) : clockedInList.length === 0 ? (
                    <div className="empty-state-card">
                      <div className="empty-icon">👥</div>
                      <p className="empty-text">No employees currently clocked in</p>
                    </div>
                  ) : (
                    <div className="kanban-employee-list">
                      {clockedInList.map(renderEmployeeCard)}
                    </div>
                  )}
                </div>
              </div>

              <div className="kanban-column clocked-out-column">
                <div className="column-header">
                  <div className="column-icon clocked-out-icon">●</div>
                  <h2 className="column-title">Recently Clocked Out</h2>
                  <span className="column-count">
                    {loading ? '—' : recentlyClockedOutList.length}
                  </span>
                </div>
                <div className="column-content">
                  {loading ? (
                    <div className="empty-state-card">
                      <p className="empty-text">Loading...</p>
                    </div>
                  ) : recentlyClockedOutList.length === 0 ? (
                    <div className="empty-state-card">
                      <div className="empty-icon">🚶</div>
                      <p className="empty-text">No recent clock-outs in the last 24h</p>
                    </div>
                  ) : (
                    <div className="kanban-employee-list">
                      {recentlyClockedOutList.map(renderEmployeeCard)}
                    </div>
                  )}
                </div>
              </div>

              <div className="kanban-column inactive-column">
                <div className="column-header">
                  <div className="column-icon inactive-icon">●</div>
                  <h2 className="column-title">Inactive</h2>
                  <span className="column-count">
                    {loading ? '—' : inactiveList.length}
                  </span>
                </div>
                <div className="column-content">
                  {loading ? (
                    <div className="empty-state-card">
                      <p className="empty-text">Loading...</p>
                    </div>
                  ) : inactiveList.length === 0 ? (
                    <div className="empty-state-card">
                      <div className="empty-icon">🏠</div>
                      <p className="empty-text">No inactive employees</p>
                    </div>
                  ) : (
                    <div className="kanban-employee-list">
                      {inactiveList.map(renderEmployeeCard)}
                    </div>
                  )}
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
