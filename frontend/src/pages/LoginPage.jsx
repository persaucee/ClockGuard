/**
 * LoginPage - Functional Login Form (Scrum 36)
 * 
 * Features:
 * - Username/password form inputs
 * - Integrated with FastAPI backend login endpoint
 * - JWT token stored in HTTP-only cookie
 * - Success: redirect to /dashboard
 * - Failure: display error message
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';
import clockGuardLogo from '../assets/CGlogo.png';
import api from '../services/apiClient';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const response = await api.auth.login({ username, password });
      
      if (response.success) {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <img src={clockGuardLogo} alt="ClockGuard Logo" />
        </div>
        <h1>Admin Dashboard</h1>
        
        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message" style={{ 
              color: '#dc3545', 
              marginBottom: '1rem', 
              padding: '0.5rem', 
              backgroundColor: '#f8d7da', 
              border: '1px solid #f5c6cb', 
              borderRadius: '4px',
              fontSize: '0.9rem'
            }}>
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              className="form-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
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
