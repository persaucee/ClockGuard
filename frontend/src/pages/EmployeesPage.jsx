import React, { useState, useEffect } from 'react';
import './EmployeesPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import PayrollTable from '../components/PayrollTable';
import { api } from '../services/apiClient';

function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [uncalculatedShifts, setUncalculatedShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [shiftsLoading, setShiftsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingTips, setEditingTips] = useState({});
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [processingPayroll, setProcessingPayroll] = useState(false);
  const [payrollMessage, setPayrollMessage] = useState(null);

  useEffect(() => {
    const fetchEmployees = async () => {
      try {
        setLoading(true);
        const data = await api.employees.getAll();
        setEmployees(data);
        setError(null);
      } catch (err) {
        setError(err.message || 'Failed to load employees');
        console.error('Error fetching employees:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEmployees();
  }, []);

  useEffect(() => {
    const fetchUncalculatedShifts = async () => {
      if (employees.length === 0) return;

      try {
        setShiftsLoading(true);
        const allSessions = [];
        
        for (const employee of employees) {
          try {
            const sessions = await api.payroll.getEmployeeSessions(employee.id);
            const uncalculated = sessions.filter(session => !session.processed);
            
            uncalculated.forEach(session => {
              allSessions.push({
                ...session,
                employee_name: employee.name,
              });
            });
          } catch (err) {
            console.error(`Error fetching sessions for employee ${employee.id}:`, err);
          }
        }

        allSessions.sort((a, b) => new Date(b.shift_date) - new Date(a.shift_date));
        setUncalculatedShifts(allSessions);
      } catch (err) {
        console.error('Error fetching uncalculated shifts:', err);
      } finally {
        setShiftsLoading(false);
      }
    };

    fetchUncalculatedShifts();
  }, [employees]);

  const handleEmployeeUpdate = (updatedEmployee) => {
    setEmployees(prevEmployees =>
      prevEmployees.map(emp =>
        emp.id === updatedEmployee.id
          ? { ...emp, name: updatedEmployee.name, hourly_rate: updatedEmployee.hourly_rate }
          : emp
      )
    );
  };

  const handleTipChange = (sessionId, value) => {
    setEditingTips(prev => ({
      ...prev,
      [sessionId]: value,
    }));
  };

  const handleTipBlur = async (session) => {
    const newTipValue = editingTips[session.id];
    
    if (newTipValue === undefined || newTipValue === '') {
      return;
    }

    const tipAmount = parseFloat(newTipValue);
    if (isNaN(tipAmount) || tipAmount < 0) {
      alert('Please enter a valid tip amount');
      setEditingTips(prev => {
        const updated = { ...prev };
        delete updated[session.id];
        return updated;
      });
      return;
    }

    if (tipAmount === (session.tip_amount || 0)) {
      return;
    }

    try {
      const updatedSession = await api.payroll.updateSession(session.id, {
        employee_id: session.employee_id,
        shift_date: session.shift_date,
        clock_in_time: session.clock_in_time,
        clock_out_time: session.clock_out_time,
        total_hours: session.total_hours,
        tip_amount: tipAmount,
        total_pay: session.total_pay,
      });

      setUncalculatedShifts(prev =>
        prev.map(s =>
          s.id === session.id
            ? { ...s, tip_amount: tipAmount }
            : s
        )
      );

      setEditingTips(prev => {
        const updated = { ...prev };
        delete updated[session.id];
        return updated;
      });
    } catch (err) {
      alert('Failed to update tip amount: ' + err.message);
      setEditingTips(prev => {
        const updated = { ...prev };
        delete updated[session.id];
        return updated;
      });
    }
  };

  const handleRunPayroll = async () => {
    if (!startDate || !endDate) {
      setPayrollMessage({ type: 'error', text: 'Please select both start and end dates.' });
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setPayrollMessage({ type: 'error', text: 'Start date must be before or equal to end date.' });
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to run payroll for the period from ${startDate} to ${endDate}? This will process all uncalculated shifts and send pay stub emails.`
    );

    if (!confirmed) {
      return;
    }

    try {
      setProcessingPayroll(true);
      setPayrollMessage(null);

      const result = await api.payroll.processPayroll(startDate, endDate);

      setPayrollMessage({ type: 'success', text: result.message || 'Payroll processed successfully.' });
      setStartDate('');
      setEndDate('');

      const allSessions = [];
      for (const employee of employees) {
        try {
          const sessions = await api.payroll.getEmployeeSessions(employee.id);
          const uncalculated = sessions.filter(session => !session.processed);
          uncalculated.forEach(session => {
            allSessions.push({
              ...session,
              employee_name: employee.name,
            });
          });
        } catch (err) {
          console.error(`Error fetching sessions for employee ${employee.id}:`, err);
        }
      }
      allSessions.sort((a, b) => new Date(b.shift_date) - new Date(a.shift_date));
      setUncalculatedShifts(allSessions);
    } catch (err) {
      setPayrollMessage({ type: 'error', text: err.message || 'Failed to process payroll.' });
    } finally {
      setProcessingPayroll(false);
    }
  };

  const formatDateTime = (dateTime) => {
    if (!dateTime) return 'N/A';
    const date = new Date(dateTime);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="employees-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <h1>Employees</h1>
            {loading && <p>Loading employees...</p>}
            {error && <p style={{ color: 'red' }}>Error: {error}</p>}
            {!loading && !error && (
              <>
                <PayrollTable 
                  employees={employees} 
                  onEmployeeUpdate={handleEmployeeUpdate}
                />
                
                <div className="run-payroll-section">
                  <h2>Run Payroll</h2>
                  <div className="payroll-controls">
                    <div className="date-inputs">
                      <div className="date-input-group">
                        <label htmlFor="start-date">Start Date</label>
                        <input
                          type="date"
                          id="start-date"
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          disabled={processingPayroll}
                        />
                      </div>
                      <div className="date-input-group">
                        <label htmlFor="end-date">End Date</label>
                        <input
                          type="date"
                          id="end-date"
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          disabled={processingPayroll}
                        />
                      </div>
                    </div>
                    <button
                      className="run-payroll-btn"
                      onClick={handleRunPayroll}
                      disabled={processingPayroll || !startDate || !endDate}
                    >
                      {processingPayroll ? 'Processing...' : 'Run Payroll'}
                    </button>
                  </div>
                  {payrollMessage && (
                    <div className={`payroll-message ${payrollMessage.type}`}>
                      {payrollMessage.text}
                    </div>
                  )}
                </div>
                
                <div className="uncalculated-shifts-section">
                  <h2>Uncalculated Shifts</h2>
                  {shiftsLoading && <p>Loading shifts...</p>}
                  {!shiftsLoading && uncalculatedShifts.length === 0 && (
                    <p className="empty-message">No uncalculated shifts found.</p>
                  )}
                  {!shiftsLoading && uncalculatedShifts.length > 0 && (
                    <div className="shifts-table-container">
                      <table className="shifts-table">
                        <thead>
                          <tr>
                            <th>Employee Name</th>
                            <th>Shift Date</th>
                            <th>Clock In</th>
                            <th>Clock Out</th>
                            <th>Total Hours</th>
                            <th>Tips</th>
                          </tr>
                        </thead>
                        <tbody>
                          {uncalculatedShifts.map((shift) => (
                            <tr key={shift.id}>
                              <td>{shift.employee_name}</td>
                              <td>{formatDate(shift.shift_date)}</td>
                              <td>{formatDateTime(shift.clock_in_time)}</td>
                              <td>{formatDateTime(shift.clock_out_time)}</td>
                              <td>{shift.total_hours?.toFixed(2) || '0.00'}</td>
                              <td>
                                <input
                                  type="number"
                                  step="0.01"
                                  min="0"
                                  className="tip-input"
                                  value={
                                    editingTips[shift.id] !== undefined
                                      ? editingTips[shift.id]
                                      : shift.tip_amount || ''
                                  }
                                  onChange={(e) => handleTipChange(shift.id, e.target.value)}
                                  onBlur={() => handleTipBlur(shift)}
                                  placeholder="0.00"
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default EmployeesPage;
