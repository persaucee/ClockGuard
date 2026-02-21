/**
 * LoginPage - Branded Placeholder
 * 
 * Scrum 10 will implement the full login UI with:
 * - Email/password form
 * - Sign In button
 * - Authentication logic
 */

import React from 'react';
import './LoginPage.css';
import clockGuardLogo from '../assets/CGlogo.png';

function LoginPage() {
  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <img src={clockGuardLogo} alt="ClockGuard Logo" />
        </div>
        <h1>Admin Dashboard</h1>
        <p className="login-placeholder">
          Login form coming in Scrum 10
        </p>
        <div className="login-button-preview">
          <button className="btn-primary" disabled>
            Sign In (Preview)
          </button>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
