import React, { useState, useEffect, useMemo } from 'react';
import './AttendanceLogsPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { api } from '../services/apiClient';
import blobAccent from '../assets/Images/Blob.png';

function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0].toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function AttendanceLogsPage() {
  const [logs, setLogs] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedEmployees, setExpandedEmployees] = useState(new Set());

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [allLogs, allEmployees] = await Promise.all([
          api.attendance.getAllLogs(),
          api.employees.getAll(),
        ]);

        allLogs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        setLogs(allLogs);
        setEmployees(allEmployees);
      } catch (err) {
        setError(err.message || 'Failed to load data');
        console.error('Error fetching attendance data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Build a unified list: employees with logs sorted by most recent activity,
  // then employees with no logs sorted alphabetically.
  const groupedEmployees = useMemo(() => {
    const normName = (s) => (s || '').trim().toLowerCase();

    // Keyed by employee_id when available, otherwise by normalized name.
    const groups = {};
    const groupsByName = {};

    logs.forEach((log) => {
      const key = log.employee_id || normName(log.employee_name);
      if (!groups[key]) {
        const g = {
          key,
          employeeId: log.employee_id || null,
          name: log.employee_name || '',
          logs: [],
        };
        groups[key] = g;
        const nk = normName(log.employee_name);
        if (nk && !groupsByName[nk]) groupsByName[nk] = g;
      }
      groups[key].logs.push(log);
    });

    Object.values(groups).forEach((g) => {
      g.logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      g.latestLog = g.logs[0];
      g.count = g.logs.length;
    });

    // Seed with every known employee so zero-log employees still appear.
    // Match by employee_id first, then normalized name.
    employees.forEach((emp) => {
      const empId = emp.employee_id || emp.id || null;
      const empName = emp.name || emp.employee_name || '';
      const nk = normName(empName);

      const existing = (empId && groups[empId]) || groupsByName[nk];

      if (existing) {
        if (!existing.employeeId && empId) existing.employeeId = empId;
        if (empName && normName(existing.name) !== nk) existing.name = empName;
      } else {
        const key = empId || nk || empName;
        groups[key] = {
          key,
          employeeId: empId,
          name: empName || 'Unknown',
          logs: [],
          latestLog: null,
          count: 0,
        };
      }
    });

    const withLogs = Object.values(groups)
      .filter((g) => g.count > 0)
      .sort((a, b) => new Date(b.latestLog.timestamp) - new Date(a.latestLog.timestamp));

    const withoutLogs = Object.values(groups)
      .filter((g) => g.count === 0)
      .sort((a, b) => (a.name || '').localeCompare(b.name || ''));

    return [...withLogs, ...withoutLogs];
  }, [logs, employees]);

  const toggleEmployee = (key) => {
    setExpandedEmployees((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const formatDate = (timestamp) =>
    new Date(timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  const formatTime = (timestamp) =>
    new Date(timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const formatHeaderDate = (timestamp) =>
    new Date(timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });

  return (
    <div className="attendance-logs-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <section className="logs-hero">
              <img
                src={blobAccent}
                alt=""
                className="logs-hero-blob"
                aria-hidden="true"
              />
              <div className="logs-hero-meta">
                <span className="section-index">[ 02 ] · ATTENDANCE</span>
                {!loading && !error && (
                  <span className="logs-page-count">
                    {groupedEmployees.length} EMPLOYEES
                  </span>
                )}
              </div>
              <h1 className="logs-hero-title">
                EVERY<br />
                <span className="display-title--silver">CLOCK MARK.</span>
              </h1>
              <p className="logs-hero-lede">
                A continuous record of every verified clock event grouped by
                employee — expand any name to walk through their full timeline.
              </p>
            </section>

            {loading && (
              <div className="logs-state-box">
                <div className="logs-spinner" />
                <p>Loading attendance logs…</p>
              </div>
            )}

            {error && (
              <div className="logs-error-box">
                <span className="logs-error-icon">⚠</span>
                <p>{error}</p>
              </div>
            )}

            {!loading && !error && groupedEmployees.length === 0 && (
              <div className="logs-state-box">
                <p className="logs-empty-text">No employees or attendance logs found.</p>
              </div>
            )}

            {!loading && !error && groupedEmployees.length > 0 && (
              <div className="employee-card-list">
                {groupedEmployees.map((employee) => {
                  const isExpanded = expandedEmployees.has(employee.key);
                  const initials = getInitials(employee.name);
                  const hasLogs = employee.count > 0;
                  const actionKey = hasLogs
                    ? employee.latestLog.action.toLowerCase()
                    : 'none';

                  return (
                    <div
                      key={employee.key}
                      className={`employee-card${isExpanded ? ' employee-card--open' : ''}${!hasLogs ? ' employee-card--no-logs' : ''}`}
                    >
                      <button
                        className="employee-card__header"
                        onClick={() => hasLogs && toggleEmployee(employee.key)}
                        aria-expanded={isExpanded}
                        disabled={!hasLogs}
                      >
                        <div className={`employee-avatar avatar--${actionKey}`}>
                          {initials}
                        </div>

                        <div className="employee-card__info">
                          <span className="employee-card__name">{employee.name}</span>
                          <span className="employee-card__meta">
                            {hasLogs
                              ? `Last activity · ${formatHeaderDate(employee.latestLog.timestamp)}`
                              : 'No activity recorded'}
                          </span>
                        </div>

                        <div className="employee-card__right">
                          {hasLogs ? (
                            <>
                              <span className={`action-badge action-${actionKey}`}>
                                {employee.latestLog.action}
                              </span>
                              <span className="employee-card__time">
                                {formatTime(employee.latestLog.timestamp)}
                              </span>
                              <span className="employee-card__log-count">
                                {employee.count} {employee.count === 1 ? 'log' : 'logs'}
                              </span>
                              <span
                                className={`employee-card__chevron${isExpanded ? ' employee-card__chevron--open' : ''}`}
                              >
                                ›
                              </span>
                            </>
                          ) : (
                            <span className="employee-card__no-logs-label">No logs</span>
                          )}
                        </div>
                      </button>

                      {isExpanded && hasLogs && (
                        <div className="employee-timeline">
                          <div className="timeline-track">
                            {employee.logs.map((log, index) => {
                              const logAction = log.action.toLowerCase();
                              return (
                                <div
                                  key={log.id || `${log.employee_id}-${log.timestamp}-${index}`}
                                  className="timeline-item"
                                >
                                  <div className="timeline-rail">
                                    <div className={`timeline-dot timeline-dot--${logAction}`} />
                                    {index < employee.logs.length - 1 && (
                                      <div className="timeline-line" />
                                    )}
                                  </div>
                                  <div className="timeline-body">
                                    <span
                                      className={`action-badge action-badge--sm action-${logAction}`}
                                    >
                                      {log.action}
                                    </span>
                                    <span className="timeline-date">{formatDate(log.timestamp)}</span>
                                    <span className="timeline-time">{formatTime(log.timestamp)}</span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default AttendanceLogsPage;
