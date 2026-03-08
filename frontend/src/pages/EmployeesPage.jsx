import React, { useState, useEffect } from 'react';
import './EmployeesPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import PayrollTable from '../components/PayrollTable';
import { api } from '../services/apiClient';

function EmployeesPage() {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  const handleEmployeeUpdate = (updatedEmployee) => {
    setEmployees(prevEmployees =>
      prevEmployees.map(emp =>
        emp.id === updatedEmployee.id
          ? { ...emp, name: updatedEmployee.name, hourly_rate: updatedEmployee.hourly_rate }
          : emp
      )
    );
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
              <PayrollTable 
                employees={employees} 
                onEmployeeUpdate={handleEmployeeUpdate}
              />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

export default EmployeesPage;
