import React, { useState, useEffect, useMemo } from 'react';
import './DashboardPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { api } from '../services/apiClient';
import faceVisual from '../assets/Images/CGface.png';
import blobOne from '../assets/Images/Blob.png';
import blobTwo from '../assets/Images/Blob2.png';
import bgChrome from '../assets/Images/bgcg.png';

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

  const renderEmployeeCard = (emp, kind) => {
    const id = getEmployeeId(emp);
    const name = getEmployeeName(emp);
    return (
      <div key={id || name} className={`person-card person-card--${kind}`}>
        <div className="person-card__avatar">{getInitials(name)}</div>
        <div className="person-card__body">
          <span className="person-card__name">{name}</span>
          {id && <span className="person-card__id">ID · {id}</span>}
        </div>
        <span className="person-card__chip">{kind === 'in' ? 'ACTIVE' : kind === 'out' ? 'OUT · 24H' : 'OFFLINE'}</span>
      </div>
    );
  };

  return (
    <div className="dashboard-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="dashboard-shell">
            <section className="hero">
              <div className="hero-meta">
                <span className="hero-meta-tag">
                  <span
                    className={`hero-dot${isConnected ? ' hero-dot--live' : ''}`}
                  />
                  {isConnected ? 'LIVE · BIOMETRIC FEED' : 'CONNECTING…'}
                </span>
                <span className="hero-meta-id">[ 01 ] · COMMAND</span>
              </div>

              <h1 className="hero-title">LIVE METRICS</h1>

              <div className="hero-stage">
                <div
                  className="hero-stage__bg"
                  style={{ backgroundImage: `url(${bgChrome})` }}
                  aria-hidden="true"
                />
                <div className="hero-stage__overlay" aria-hidden="true" />

                <div className="hero-stage__corner hero-stage__corner--left">
                  <span className="hero-stage__corner-label">Active</span>
                  <span className="hero-stage__corner-value">
                    {loading ? '—' : String(clockedInList.length).padStart(2, '0')}
                  </span>
                </div>

                <div className="hero-stage__corner hero-stage__corner--right">
                  <p className="hero-stage__lede">
                    Real-time facial verification and attendance intelligence
                    streamed onto a single command surface.
                  </p>
                  <div className="hero-stage__meta-grid">
                    <span>
                      <em>Inactive</em>
                      <strong>
                        {loading ? '—' : String(inactiveList.length).padStart(2, '0')}
                      </strong>
                    </span>
                    <span>
                      <em>Channel</em>
                      <strong>{isConnected ? 'ONLINE' : 'OFFLINE'}</strong>
                    </span>
                  </div>
                </div>

                <img
                  src={blobOne}
                  alt=""
                  className="hero-blob hero-blob--top"
                  aria-hidden="true"
                />
              </div>

              <img
                src={faceVisual}
                alt=""
                className="hero-face"
                aria-hidden="true"
              />
            </section>

            {error && (
              <div className="dashboard-error">
                <span>⚠</span> {error}
              </div>
            )}

            <section className="numbers-section">
              <div className="numbers-section__head">
                <span className="section-index">[ 03 ] · TODAY</span>
              </div>

              <div className="numbers-grid">
                <div className="number-card number-card--accent">
                  <span className="number-card__label">Clocked In</span>
                  <span className="number-card__value">
                    {loading ? '—' : String(clockedInList.length).padStart(2, '0')}
                  </span>
                  <span className="number-card__hint">Currently active</span>
                </div>
                <div className="number-card">
                  <span className="number-card__label">Recently Out</span>
                  <span className="number-card__value">
                    {loading ? '—' : String(recentlyClockedOutList.length).padStart(2, '0')}
                  </span>
                  <span className="number-card__hint">Last 24 hours</span>
                </div>
                <div className="number-card">
                  <span className="number-card__label">Inactive</span>
                  <span className="number-card__value">
                    {loading ? '—' : String(inactiveList.length).padStart(2, '0')}
                  </span>
                  <span className="number-card__hint">No recent activity</span>
                </div>
              </div>
            </section>

            <div className="chrome-strip" aria-hidden="true">
              <div
                className="chrome-strip__bg"
                style={{ backgroundImage: `url(${bgChrome})` }}
              />
              <span className="chrome-strip__label">
                ACTIVE PULSE · LIVE BIOMETRIC FEED · {isConnected ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>

            <section className="feed-section">
              <div className="feed-section__head">
                <span className="section-index">[ 04 ] · LIVE FEED</span>
                <h2 className="feed-section__title">
                  LIVE<br />
                  <span className="display-title--silver">FEED.</span>
                </h2>
                <span
                  className={`feed-section__pulse${isConnected ? ' feed-section__pulse--on' : ''}`}
                  aria-hidden="true"
                />
              </div>

              <div className="feed-list-wrap">
                {loading ? (
                  <div className="feed-empty">
                    <span className="feed-empty__icon">⏳</span>
                    <p>Loading activity feed…</p>
                  </div>
                ) : groupedActivities.length === 0 ? (
                  <div className="feed-empty">
                    <span className="feed-empty__icon">⌖</span>
                    <p>
                      {isConnected
                        ? 'Waiting for live scanner activity…'
                        : 'Connecting to live feed…'}
                    </p>
                  </div>
                ) : (
                  <ul className="feed-list">
                    {groupedActivities.map((group) => {
                      const isExpanded = expandedFeedEmployees.has(group.key);
                      const latestAction = group.latestEvent.action.toLowerCase();
                      return (
                        <li
                          key={group.key}
                          className={`feed-row${isExpanded ? ' feed-row--open' : ''}`}
                        >
                          <button
                            className="feed-row__main"
                            onClick={() => toggleFeedEmployee(group.key)}
                            aria-expanded={isExpanded}
                          >
                            <span className={`feed-row__avatar feed-row__avatar--${latestAction}`}>
                              {getInitials(group.employeeName)}
                            </span>
                            <span className="feed-row__name">{group.employeeName}</span>
                            <span className="feed-row__count">
                              {group.events.length} {group.events.length === 1 ? 'event' : 'events'}
                            </span>
                            <span className={`feed-row__badge feed-row__badge--${latestAction}`}>
                              {group.latestEvent.action === 'IN' ? 'CLOCKED IN' : 'CLOCKED OUT'}
                            </span>
                            <span className="feed-row__time">
                              {formatTimestamp(group.latestEvent.timestamp)}
                            </span>
                            <span
                              className={`feed-row__chevron${isExpanded ? ' feed-row__chevron--open' : ''}`}
                              aria-hidden="true"
                            >
                              →
                            </span>
                          </button>

                          {isExpanded && (
                            <div className="feed-timeline">
                              {group.events.map((event, index) => (
                                <div key={event.id} className="feed-timeline__item">
                                  <div className="feed-timeline__rail">
                                    <span
                                      className={`feed-timeline__dot feed-timeline__dot--${event.action.toLowerCase()}`}
                                    />
                                    {index < group.events.length - 1 && (
                                      <span className="feed-timeline__line" />
                                    )}
                                  </div>
                                  <div className="feed-timeline__body">
                                    <span
                                      className={`feed-row__badge feed-row__badge--${event.action.toLowerCase()}`}
                                    >
                                      {event.action}
                                    </span>
                                    <span className="feed-timeline__date">
                                      {formatDate(event.timestamp)}
                                    </span>
                                    <span className="feed-row__time">
                                      {formatTimestamp(event.timestamp)}
                                    </span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </section>

            <section className="workforce-section">
              <img
                src={blobTwo}
                alt=""
                className="workforce-blob"
                aria-hidden="true"
              />
              <div className="workforce-section__head">
                <div className="workforce-section__head-left">
                  <span className="section-index">[ 05 ] · ROSTER</span>
                  <h2 className="workforce-section__title">
                    KNOW<br />
                    <span className="display-title--chrome">WHO IS</span><br />
                    ON THE FLOOR.
                  </h2>
                </div>
                <p className="workforce-section__lede">
                  A rolling view of who's active, who's just left, and who has
                  been off the schedule — all updated the moment a verification
                  fires.
                </p>
              </div>

              <div className="workforce-grid">
                <div className="workforce-col workforce-col--in">
                  <div className="workforce-col__head">
                    <span className="workforce-col__index">01</span>
                    <span className="workforce-col__title">CLOCKED IN</span>
                    <span className="workforce-col__count">
                      {loading ? '—' : clockedInList.length}
                    </span>
                  </div>
                  <div className="workforce-col__body">
                    {loading ? (
                      <div className="workforce-empty">
                        <p>Loading…</p>
                      </div>
                    ) : clockedInList.length === 0 ? (
                      <div className="workforce-empty">
                        <p>No employees currently clocked in</p>
                      </div>
                    ) : (
                      <div className="workforce-list">
                        {clockedInList.map((emp) => renderEmployeeCard(emp, 'in'))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="workforce-col workforce-col--out">
                  <div className="workforce-col__head">
                    <span className="workforce-col__index">02</span>
                    <span className="workforce-col__title">RECENTLY OUT</span>
                    <span className="workforce-col__count">
                      {loading ? '—' : recentlyClockedOutList.length}
                    </span>
                  </div>
                  <div className="workforce-col__body">
                    {loading ? (
                      <div className="workforce-empty">
                        <p>Loading…</p>
                      </div>
                    ) : recentlyClockedOutList.length === 0 ? (
                      <div className="workforce-empty">
                        <p>No clock-outs in the last 24h</p>
                      </div>
                    ) : (
                      <div className="workforce-list">
                        {recentlyClockedOutList.map((emp) => renderEmployeeCard(emp, 'out'))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="workforce-col workforce-col--inactive">
                  <div className="workforce-col__head">
                    <span className="workforce-col__index">03</span>
                    <span className="workforce-col__title">INACTIVE</span>
                    <span className="workforce-col__count">
                      {loading ? '—' : inactiveList.length}
                    </span>
                  </div>
                  <div className="workforce-col__body">
                    {loading ? (
                      <div className="workforce-empty">
                        <p>Loading…</p>
                      </div>
                    ) : inactiveList.length === 0 ? (
                      <div className="workforce-empty">
                        <p>No inactive employees</p>
                      </div>
                    ) : (
                      <div className="workforce-list">
                        {inactiveList.map((emp) => renderEmployeeCard(emp, 'inactive'))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </section>

            <footer className="dashboard-foot">
              <div
                className="dashboard-foot__chrome"
                style={{ backgroundImage: `url(${bgChrome})` }}
                aria-hidden="true"
              />
              <span className="dashboard-foot__brand">CLOCKGUARD</span>
              <span className="dashboard-foot__copy">
                BIOMETRIC ATTENDANCE · POWERED BY FACIAL VERIFICATION
              </span>
            </footer>
          </div>
        </main>
      </div>
    </div>
  );
}

export default DashboardPage;
