import React from 'react';
import './PayrollTable.css';

function PayrollTable({ employees }) {
  return (
    <div className="payroll-table-container">
      <table className="payroll-table">
        <thead>
          <tr>
            <th>Employee Name</th>
            <th>Wage Rate</th>
            <th>Total Hours</th>
            <th>Total Pay</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee.id}>
              <td>{employee.name}</td>
              <td>${employee.wageRate.toFixed(2)}/hr</td>
              <td>{employee.totalHours.toFixed(2)}</td>
              <td>${(employee.wageRate * employee.totalHours).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default PayrollTable;
