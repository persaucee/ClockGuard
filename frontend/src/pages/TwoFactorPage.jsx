import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css';
import api from '../services/apiClient';

function TwoFactorPage() {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const tempToken = sessionStorage.getItem('temp_token');

    if (!tempToken) {
      navigate('/login');
    }
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const tempToken = sessionStorage.getItem('temp_token');

      if (!tempToken) {
        setError('Session expired. Please log in again.');
        navigate('/login');
        return;
      }

      const response = await api.auth.verify2FA(tempToken, code);

      sessionStorage.removeItem('temp_token');

      if (response.success) {
        navigate('/dashboard');
        return;
      }

      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Invalid authentication code.');
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Two-Factor Authentication</h1>
        <p style={{ marginBottom: '1rem', textAlign: 'center' }}>
          Enter the 6-digit code from your authenticator app.
        </p>

        <form className="login-form" onSubmit={handleSubmit}>
          {error && (
            <div
              className="error-message"
              style={{
                color: '#dc3545',
                marginBottom: '1rem',
                padding: '0.5rem',
                backgroundColor: '#f8d7da',
                border: '1px solid #f5c6cb',
                borderRadius: '4px',
                fontSize: '0.9rem'
              }}
            >
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="code">Authentication Code</label>
            <input
              type="text"
              id="code"
              className="form-input"
              placeholder="Enter 6-digit code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={6}
              required
            />
          </div>

          <button type="submit" className="btn-primary btn-login">
            Verify Code
          </button>
        </form>
      </div>
    </div>
  );
}

export default TwoFactorPage;