import React, { useState, useEffect } from 'react';
import './AttendanceLogsPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import { api } from '../services/apiClient';

function AttendanceLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAttendanceLogs = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await api.attendance.getLogs();
        const sessions = response.data || [];

        const logEntries = [];
        sessions.forEach(session => {
          if (session.clock_in_time) {
            logEntries.push({
              id: `${session.id}-in`,
              employee_name: session.employee_name,
              action: 'IN',
              timestamp: session.clock_in_time
            });
          }
          if (session.clock_out_time) {
            logEntries.push({
              id: `${session.id}-out`,
              employee_name: session.employee_name,
              action: 'OUT',
              timestamp: session.clock_out_time
            });
          }
        });

        logEntries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        setLogs(logEntries);
      } catch (err) {
        setError(err.message || 'Failed to load attendance logs');
        console.error('Error fetching attendance logs:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAttendanceLogs();
  }, []);

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="attendance-logs-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <h1>Attendance Logs</h1>
            
            {loading && <p className="loading-message">Loading attendance logs...</p>}
            
            {error && <p className="error-message">Error: {error}</p>}
            
            {!loading && !error && logs.length === 0 && (
              <p className="empty-message">No attendance logs found.</p>
            )}
            
            {!loading && !error && logs.length > 0 && (
              <div className="attendance-table-container">
                <table className="attendance-table">
                  <thead>
                    <tr>
                      <th>Employee Name</th>
                      <th>Action</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id || `${log.employee_id}-${log.timestamp}`}>
                        <td>{log.employee_name}</td>
                        <td>
                          <span className={`action-badge action-${log.action.toLowerCase()}`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="timestamp-cell">{formatTimestamp(log.timestamp)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default AttendanceLogsPage;
