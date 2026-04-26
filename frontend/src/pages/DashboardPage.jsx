import React, { useState, useEffect, useMemo } from 'react';
import './DashboardPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { api } from '../services/apiClient';
import faceVisual from '../assets/Images/CGface.png';
import blobOne from '../assets/Images/Blob.png';
import bgChrome from '../assets/Images/bgcg.png';

function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getEmployeeId(emp) {
  if (emp == null) return null;
  return emp.employee_id ?? emp.id ?? null;
}

function getEmployeeName(emp) {
  return emp?.name || emp?.employee_name || 'Unknown';
}

function sameEmployeeId(a, b) {
  if (a == null || b == null) return false;
  return String(a) === String(b);
}

function normName(s) {
  return (s || '').trim().toLowerCase();
}

/**
 * Clocked in = latest log per person is IN.
 * Not clocked in = latest is OUT, or no logs. Sub-kind for UI chip: out | no_logs.
 */
function deriveRosterFromLogs(employees, logs) {
  const latestById = new Map();
  const latestByName = new Map();

  for (const log of logs) {
    const ts = new Date(log.timestamp).getTime();
    if (Number.isNaN(ts)) continue;
    if (log.employee_id != null && log.employee_id !== '') {
      const k = String(log.employee_id);
      const prev = latestById.get(k);
      if (!prev || ts > new Date(prev.timestamp).getTime()) {
        latestById.set(k, log);
      }
    } else {
      const nk = normName(log.employee_name);
      if (!nk) continue;
      const prev = latestByName.get(nk);
      if (!prev || ts > new Date(prev.timestamp).getTime()) {
        latestByName.set(nk, log);
      }
    }
  }

  const clockedIn = [];
  const notClockedIn = [];

  for (const emp of employees) {
    const id = getEmployeeId(emp);
    const name = getEmployeeName(emp);
    const nk = normName(name);
    let latest = null;
    if (id != null) latest = latestById.get(String(id));
    if (!latest) latest = latestByName.get(nk);

    const action = String(latest?.action || '').toUpperCase();
    const row = {
      name,
      employee_id: id,
      email: emp.email,
    };
    if (!latest) {
      notClockedIn.push({ ...row, notClockedInKind: 'no_logs' });
    } else if (action === 'IN') {
      clockedIn.push(row);
    } else {
      notClockedIn.push({ ...row, notClockedInKind: 'out' });
    }
  }

  const byName = (a, b) => a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
  clockedIn.sort(byName);
  notClockedIn.sort(byName);

  return { clockedIn, notClockedIn };
}

const NOT_CLOCKED_IN_PREVIEW = 5;

function DashboardPage() {
  const [clockedInList, setClockedInList] = useState([]);
  const [notClockedInList, setNotClockedInList] = useState([]);
  const [activities, setActivities] = useState([]);
  const [expandedFeedEmployees, setExpandedFeedEmployees] = useState(new Set());
  const [notClockedInExpanded, setNotClockedInExpanded] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (notClockedInList.length <= NOT_CLOCKED_IN_PREVIEW) {
      setNotClockedInExpanded(false);
    }
  }, [notClockedInList.length]);

  // Initial data fetch
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [allLogs, employees] = await Promise.all([
          api.attendance.getAllLogs(),
          api.employees.getAll(),
        ]);

        allLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        const { clockedIn, notClockedIn } = deriveRosterFromLogs(employees, allLogs);
        setClockedInList(clockedIn);
        setNotClockedInList(notClockedIn);

        // Only show the 50 most recent events in the activity feed
        const initialActivities = allLogs.slice(0, 50).map((log, i) => ({
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

        const eid = data.match.employee_id;
        const employeeEntry = {
          name: data.match.name || 'Unknown',
          employee_id: eid,
          email: data.match.email,
        };
        const notInEntry = { ...employeeEntry, notClockedInKind: 'out' };

        if (data.action === 'IN') {
          setClockedInList((prev) => {
            if (eid == null) return prev;
            const has = prev.some((e) => sameEmployeeId(getEmployeeId(e), eid));
            if (has) return prev;
            return [employeeEntry, ...prev].sort((a, b) =>
              a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
            );
          });
          setNotClockedInList((prev) =>
            prev.filter((e) => !sameEmployeeId(getEmployeeId(e), eid))
          );
        } else if (data.action === 'OUT') {
          setClockedInList((prev) =>
            eid == null
              ? prev
              : prev.filter((e) => !sameEmployeeId(getEmployeeId(e), eid))
          );
          setNotClockedInList((prev) => {
            if (eid == null) return prev;
            if (prev.some((e) => sameEmployeeId(getEmployeeId(e), eid))) {
              return prev.map((e) =>
                sameEmployeeId(getEmployeeId(e), eid) ? { ...e, ...notInEntry } : e
              );
            }
            return [...prev, notInEntry].sort((a, b) =>
              a.name.localeCompare(b.name, undefined, { sensitivity: 'base' })
            );
          });
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
    const isIn = emp.notClockedInKind == null;
    const variant = isIn
      ? 'in'
      : emp.notClockedInKind === 'out'
        ? 'out'
        : 'nologs';
    const chip = isIn
      ? 'ACTIVE'
      : emp.notClockedInKind === 'out'
        ? 'OUT'
        : 'NO LOGS';
    return (
      <div
        key={id != null ? String(id) : name}
        className={`person-card person-card--${variant}`}
      >
        <div className="person-card__avatar">{getInitials(name)}</div>
        <div className="person-card__body">
          <span className="person-card__name">{name}</span>
          {id && <span className="person-card__id">ID · {id}</span>}
        </div>
        <span className="person-card__chip">{chip}</span>
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
            <section className="hero hero--compact">
              <h1 className="hero-title">
                LIVE <span className="display-title--chrome">METRICS</span>
              </h1>

              <div className="hero-stage">
                <div className="hero-stage__bg" aria-hidden="true" />
                <div className="hero-stage__overlay" aria-hidden="true" />

                <div className="hero-stage__corner hero-stage__corner--right">
                  <p className="hero-stage__lede">
                    Real-time facial verification and attendance intelligence
                    streamed onto a single command surface.
                  </p>
                  <div className="hero-stage__meta-grid">
                    <span>
                      <em>Channel</em>
                      <strong>{isConnected ? 'ONLINE' : 'OFFLINE'}</strong>
                    </span>
                  </div>
                </div>
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

            <div
              className="dashboard-status-twin dashboard-status-twin--post-hero"
              aria-label="Attendance headcount"
            >
              <div className="status-tile status-tile--in">
                <span className="status-tile__label">
                  Clocked <span className="display-title--chrome">in</span>
                </span>
                <span className="status-tile__value">
                  {loading ? '—' : String(clockedInList.length).padStart(2, '0')}
                </span>
              </div>
              <div className="status-tile">
                <span className="status-tile__label">
                  Not clocked <span className="display-title--chrome">in</span>
                </span>
                <span className="status-tile__value">
                  {loading ? '—' : String(notClockedInList.length).padStart(2, '0')}
                </span>
              </div>
            </div>

            <section className="feed-section">
              <div className="feed-section__head">
                <h2 className="feed-section__title dashboard-section-title">
                  Live <span className="display-title--chrome">Feed</span>
                </h2>
                <span
                  className={`feed-section__pulse${isConnected ? ' feed-section__pulse--on' : ''}`}
                  title={isConnected ? 'Live' : 'Connecting'}
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

            <section
              className="workforce-section"
              style={{ '--roster-chrome': `url(${bgChrome})` }}
            >
              <div
                className="workforce-section__chrome"
                style={{ backgroundImage: `url(${bgChrome})` }}
                aria-hidden="true"
              />
              <div className="workforce-section__head">
                <img
                  src={blobOne}
                  alt=""
                  className="workforce-title-blob"
                  aria-hidden="true"
                />
                <h2 className="workforce-section__title dashboard-section-title dashboard-section-title--roster">
                  Roster
                </h2>
                <img
                  src={blobOne}
                  alt=""
                  className="workforce-title-blob workforce-title-blob--mirror"
                  aria-hidden="true"
                />
              </div>
              <div className="workforce-grid">
                <div className="workforce-col workforce-col--in">
                  <div className="workforce-col__head">
                    <span className="workforce-col__title">
                      CLOCKED <span className="display-title--chrome">IN</span>
                    </span>
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
                        {clockedInList.map((emp) => renderEmployeeCard(emp))}
                      </div>
                    )}
                  </div>
                </div>

                <div className="workforce-col workforce-col--notin">
                  <div className="workforce-col__head">
                    <span className="workforce-col__title">
                      NOT CLOCKED <span className="display-title--chrome">IN</span>
                    </span>
                    <span className="workforce-col__count">
                      {loading ? '—' : notClockedInList.length}
                    </span>
                  </div>
                  <div className="workforce-col__body">
                    {loading ? (
                      <div className="workforce-empty">
                        <p>Loading…</p>
                      </div>
                    ) : notClockedInList.length === 0 ? (
                      <div className="workforce-empty">
                        <p>All roster employees are clocked in</p>
                      </div>
                    ) : (
                      <>
                        <div className="workforce-list">
                          {(notClockedInExpanded
                            ? notClockedInList
                            : notClockedInList.slice(0, NOT_CLOCKED_IN_PREVIEW)
                          ).map((emp) => renderEmployeeCard(emp))}
                        </div>
                        {notClockedInList.length > NOT_CLOCKED_IN_PREVIEW && (
                          <div className="workforce-col__more">
                            <button
                              type="button"
                              className="workforce-show-more"
                              onClick={() =>
                                setNotClockedInExpanded((prev) => !prev)
                              }
                              aria-expanded={notClockedInExpanded}
                            >
                              {notClockedInExpanded
                                ? 'Show less'
                                : `Show ${notClockedInList.length - NOT_CLOCKED_IN_PREVIEW} more`}
                            </button>
                          </div>
                        )}
                      </>
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
              <span className="dashboard-foot__brand">
                CLOCK
                <span className="display-title--chrome">GUARD</span>
              </span>
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
