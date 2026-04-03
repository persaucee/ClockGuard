import React, { useState, useEffect } from 'react';
import './SettingsPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import api from '../services/apiClient';
import { QRCodeCanvas } from 'qrcode.react';

function SettingsPage() {
  const [textSize, setTextSize] = useState(localStorage.getItem('textSize') || 'medium');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [fontFamily, setFontFamily] = useState(localStorage.getItem('fontFamily') || 'system');
  const [qrSecret, setQrSecret] = useState('');
  const [setupCode, setSetupCode] = useState('');
  const [setupMode, setSetupMode] = useState(false);
  const [message, setMessage] = useState('');
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);

  useEffect(() => {
    applyPreferences();
  }, [textSize, theme, fontFamily]);

  const fetchUser = async () => {
    try {
      const res = await api.auth.getMe();
      setIs2FAEnabled(res.data.two_factor_enabled);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const applyPreferences = () => {
    const root = document.documentElement;
    
    if (textSize === 'small') {
      root.style.fontSize = '14px';
    } else if (textSize === 'large') {
      root.style.fontSize = '18px';
    } else {
      root.style.fontSize = '16px';
    }
    
    if (theme === 'dark') {
      root.classList.add('dark-theme');
    } else {
      root.classList.remove('dark-theme');
    }
    
    if (fontFamily === 'serif') {
      root.style.fontFamily = 'Georgia, Cambria, "Times New Roman", Times, serif';
    } else if (fontFamily === 'mono') {
      root.style.fontFamily = '"Courier New", Courier, monospace';
    } else {
      root.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif';
    }
  };

  const handleTextSizeChange = (size) => {
    setTextSize(size);
    localStorage.setItem('textSize', size);
  };

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
  };

  const handleFontChange = (font) => {
    setFontFamily(font);
    localStorage.setItem('fontFamily', font);
  };

// 2FA Functions

  const handleEnable2FA = async () => {
    try {
      const res = await api.auth.initiate2FASetup();

      setQrSecret(res.data.secret);
      setSetupMode(true);
      setMessage('Scan this secret in Google Authenticator');
    } catch (err) {
      setMessage(err.message);
    }
  };

  const handleConfirm2FA = async () => {
    try {
      await api.auth.confirm2FASetup(setupCode);
      setMessage('2FA enabled successfully!');
      setSetupMode(false);
      setIs2FAEnabled(true);
      setSetupCode('');
    } catch (err) {
      setMessage(err.message);
    }
  };

  const handleDisable2FA = async () => {
    try {
      await api.auth.disable2FA();
      setIs2FAEnabled(false);
      setSetupMode(false);
      setQrSecret('');
      setSetupCode('');
      setMessage('2FA disabled successfully!');
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div className="settings-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <h1>Settings</h1>
            <p className="settings-description">Customize your dashboard experience</p>

            <div className="settings-section">
              <h2>Text Size</h2>
              <div className="setting-options">
                <button
                  className={`setting-option ${textSize === 'small' ? 'active' : ''}`}
                  onClick={() => handleTextSizeChange('small')}
                >
                  Small
                </button>
                <button
                  className={`setting-option ${textSize === 'medium' ? 'active' : ''}`}
                  onClick={() => handleTextSizeChange('medium')}
                >
                  Medium
                </button>
                <button
                  className={`setting-option ${textSize === 'large' ? 'active' : ''}`}
                  onClick={() => handleTextSizeChange('large')}
                >
                  Large
                </button>
              </div>
            </div>

            <div className="settings-section">
              <h2>Theme</h2>
              <div className="setting-options">
                <button
                  className={`setting-option ${theme === 'light' ? 'active' : ''}`}
                  onClick={() => handleThemeChange('light')}
                >
                  ☀️ Light Mode
                </button>
                <button
                  className={`setting-option ${theme === 'dark' ? 'active' : ''}`}
                  onClick={() => handleThemeChange('dark')}
                >
                  🌙 Dark Mode
                </button>
              </div>
            </div>

            <div className="settings-section">
              <h2>Font Family</h2>
              <div className="setting-options">
                <button
                  className={`setting-option ${fontFamily === 'system' ? 'active' : ''}`}
                  onClick={() => handleFontChange('system')}
                >
                  System
                </button>
                <button
                  className={`setting-option ${fontFamily === 'serif' ? 'active' : ''}`}
                  onClick={() => handleFontChange('serif')}
                >
                  Serif
                </button>
                <button
                  className={`setting-option ${fontFamily === 'mono' ? 'active' : ''}`}
                  onClick={() => handleFontChange('mono')}
                >
                  Monospace
                </button>
              </div>
            </div>

            <div className="settings-section">
              <h2>Security</h2>

              {!is2FAEnabled && !setupMode && (
                <button
                  className="setting-option"
                  onClick={handleEnable2FA}
                >
                  Enable 2FA
                </button>
              )}

              {setupMode && (
                <div style={{ marginTop: '1rem' }}>
                  <p><strong>Secret:</strong> {qrSecret}</p>

                  <QRCodeCanvas
                    value={`otpauth://totp/ClockGuard?secret=${qrSecret}&issuer=ClockGuard`}
                    size={150}
                  />

                  <p style={{ marginBottom: '0.75rem', color: '#666' }}>
                    Add this secret to Google Authenticator, then enter the 6-digit code below.
                  </p>

                  <input
                    type="text"
                    placeholder="Enter 6-digit code"
                    value={setupCode}
                    onChange={(e) => setSetupCode(e.target.value)}
                    style={{
                      marginTop: '10px',
                      padding: '8px',
                      width: '100%',
                      maxWidth: '300px'
                    }}
                  />

                  <div>
                    <button
                      className="setting-option"
                      onClick={handleConfirm2FA}
                      style={{ marginTop: '10px' }}
                    >
                      Confirm 2FA
                    </button>
                  </div>
                </div>
              )}

              {is2FAEnabled && !setupMode && (
                <div style={{ marginTop: '1rem' }}>
                  <p style={{ color: 'green', fontWeight: '500' }}>
                    2FA is enabled
                  </p>

                  <button
                    className="setting-option"
                    onClick={handleDisable2FA}
                    style={{ marginTop: '10px' }}
                  >
                    Disable 2FA
                  </button>
                </div>
              )}

              {message && (
                <p style={{ marginTop: '10px', color: 'green' }}>{message}</p>
              )}
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}

export default SettingsPage;
