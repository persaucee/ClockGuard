import React, { useState } from 'react';
import './PayrollTable.css';
import { api } from '../services/apiClient';

function PayrollTable({ employees, onEmployeeUpdate }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [formData, setFormData] = useState({ name: '', hourly_rate: '' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleEditClick = (employee) => {
    setEditingEmployee(employee);
    const rate = employee.wageRate || employee.hourly_rate || 0;
    setFormData({
      name: employee.name,
      hourly_rate: Number(rate).toFixed(2),
    });
    setError(null);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingEmployee(null);
    setFormData({ name: '', hourly_rate: '' });
    setError(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const updatedEmployee = await api.employees.update(editingEmployee.id, {
        name: formData.name,
        hourly_rate: parseFloat(formData.hourly_rate),
      });

      if (onEmployeeUpdate) {
        onEmployeeUpdate(updatedEmployee);
      }

      handleCloseModal();
    } catch (err) {
      setError(err.message || 'Failed to update employee');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div className="payroll-table-container">
        <table className="payroll-table">
          <thead>
            <tr>
              <th>Employee Name</th>
              <th>Email</th>
              <th>Wage Rate</th>
              <th>Total Hours</th>
              <th>Total Pay</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((employee) => {
              const wageRate = employee.wageRate || employee.hourly_rate || 0;
              const totalHours = employee.totalHours || 0;
              
              return (
                <tr key={employee.id}>
                  <td>{employee.name}</td>
                  <td>{employee.email || 'N/A'}</td>
                  <td>${wageRate.toFixed(2)}/hr</td>
                  <td>{totalHours.toFixed(2)}</td>
                  <td>${(wageRate * totalHours).toFixed(2)}</td>
                  <td>
                    <button
                      className="edit-btn"
                      onClick={() => handleEditClick(employee)}
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Edit Employee</h2>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name">Employee Name</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="hourly_rate">Hourly Rate ($)</label>
                <input
                  type="number"
                  id="hourly_rate"
                  name="hourly_rate"
                  value={formData.hourly_rate}
                  onChange={handleInputChange}
                  step="0.01"
                  min="0"
                  required
                />
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="cancel-btn"
                  onClick={handleCloseModal}
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="save-btn"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default PayrollTable;
