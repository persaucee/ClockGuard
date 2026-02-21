/**
 * EmployeesPage - Placeholder (Scrum 11)
 * 
 * Features:
 * - Navbar on top
 * - Sidebar navigation
 * - Content area with placeholder text
 */

import React from 'react';
import './EmployeesPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

function EmployeesPage() {
  return (
    <div className="employees-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <h1>Employees</h1>
            <p>Content coming in Sprint 2</p>
          </div>
        </main>
      </div>
    </div>
  );
}

export default EmployeesPage;
