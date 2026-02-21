/**
 * LoginPage - Functional Login Form (Scrum 10)
 * 
 * Features:
 * - Email/password form inputs
 * - Sign In button with console logging
 * - No API integration yet (coming in future sprints)
 */

import React, { useState } from 'react';
import './LoginPage.css';
import clockGuardLogo from '../assets/CGlogo.png';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Login Form Submitted:');
    console.log('Email:', email);
    console.log('Password:', password);
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <img src={clockGuardLogo} alt="ClockGuard Logo" />
        </div>
        <h1>Admin Dashboard</h1>
        
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              className="form-input"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary btn-login">
            Sign In
          </button>
        </form>
      </div>
    </div>
  );
}

export default LoginPage;
