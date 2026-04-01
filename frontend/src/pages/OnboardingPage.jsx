import React, { useState } from 'react';
import './OnboardingPage.css';
import clockGuardLogo from '../assets/CGlogo.png';

function OnboardingPage() {
  const [formData, setFormData] = useState({
    businessName: '',
    managerName: '',
    defaultOpenTime: '',
    defaultCloseTime: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const formatTimeToSQL = (timeString) => {
    if (!timeString) return '';
    return `${timeString}:00`;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    const formattedData = {
      businessName: formData.businessName,
      managerName: formData.managerName,
      defaultOpenTime: formatTimeToSQL(formData.defaultOpenTime),
      defaultCloseTime: formatTimeToSQL(formData.defaultCloseTime),
    };

    console.log('Onboarding data:', formattedData);
  };

  return (
    <div className="onboarding-page">
      <div className="onboarding-card">
        <div className="onboarding-logo">
          <img src={clockGuardLogo} alt="ClockGuard Logo" />
        </div>
        
        <h1>Welcome to ClockGuard</h1>
        <p className="onboarding-subtitle">
          Set up your business to get started
        </p>

        <form className="onboarding-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="businessName">Business Name</label>
            <input
              type="text"
              id="businessName"
              name="businessName"
              className="form-input"
              placeholder="Enter your business name"
              value={formData.businessName}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="managerName">Manager/Owner Name</label>
            <input
              type="text"
              id="managerName"
              name="managerName"
              className="form-input"
              placeholder="Enter your full name"
              value={formData.managerName}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="defaultOpenTime">Default Open Time</label>
              <input
                type="time"
                id="defaultOpenTime"
                name="defaultOpenTime"
                className="form-input"
                value={formData.defaultOpenTime}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="defaultCloseTime">Default Close Time</label>
              <input
                type="time"
                id="defaultCloseTime"
                name="defaultCloseTime"
                className="form-input"
                value={formData.defaultCloseTime}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <button type="submit" className="btn-primary btn-onboard">
            Complete Setup
          </button>
        </form>
      </div>
    </div>
  );
}

export default OnboardingPage;
