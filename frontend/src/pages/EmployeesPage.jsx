/**
 * EmployeesPage - Payroll Table (Scrum 33)
 * 
 * Features:
 * - Navbar on top
 * - Sidebar navigation
 * - Payroll table displaying employee wage information
 */

import React from 'react';
import './EmployeesPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import PayrollTable from '../components/PayrollTable';

const mockEmployees = [
  { id: 1, name: 'John Smith', wageRate: 25.00, totalHours: 160 },
  { id: 2, name: 'Sarah Johnson', wageRate: 30.50, totalHours: 152 },
  { id: 3, name: 'Michael Chen', wageRate: 22.75, totalHours: 168 },
  { id: 4, name: 'Emily Rodriguez', wageRate: 28.00, totalHours: 145 },
  { id: 5, name: 'David Kim', wageRate: 32.00, totalHours: 160 },
];

function EmployeesPage() {
  return (
    <div className="employees-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <h1>Employees</h1>
            <PayrollTable employees={mockEmployees} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default EmployeesPage;
