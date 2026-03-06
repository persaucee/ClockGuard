/**
 * EmployeesPage - Payroll Table (Scrum 33, Enhanced in Scrum 41)
 * 
 * Features:
 * - Navbar on top
 * - Sidebar navigation
 * - Payroll table displaying employee wage information
 * - Employee editing functionality (Scrum 41)
 */

import React, { useState } from 'react';
import './EmployeesPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import PayrollTable from '../components/PayrollTable';

const initialMockEmployees = [
  { id: 1, name: 'John Smith', email: 'john.smith@clockguard.com', wageRate: 25.00, totalHours: 160 },
  { id: 2, name: 'Sarah Johnson', email: 'sarah.johnson@clockguard.com', wageRate: 30.50, totalHours: 152 },
  { id: 3, name: 'Michael Chen', email: 'michael.chen@clockguard.com', wageRate: 22.75, totalHours: 168 },
  { id: 4, name: 'Emily Rodriguez', email: 'emily.rodriguez@clockguard.com', wageRate: 28.00, totalHours: 145 },
  { id: 5, name: 'David Kim', email: 'david.kim@clockguard.com', wageRate: 32.00, totalHours: 160 },
];

function EmployeesPage() {
  const [employees, setEmployees] = useState(initialMockEmployees);

  const handleEmployeeUpdate = (updatedEmployee) => {
    setEmployees(prevEmployees =>
      prevEmployees.map(emp =>
        emp.id === updatedEmployee.id
          ? { ...emp, name: updatedEmployee.name, wageRate: updatedEmployee.hourly_rate }
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
            <PayrollTable 
              employees={employees} 
              onEmployeeUpdate={handleEmployeeUpdate}
            />
          </div>
        </main>
      </div>
    </div>
  );
}

export default EmployeesPage;
