import React, { useState, useEffect } from 'react';
import './SettingsPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import blobAccent from '../assets/Images/Blob.png';
import api from '../services/apiClient';
import { QRCodeCanvas } from 'qrcode.react';
import {
  FONT_PRESETS,
  applyFontFamilyPreset,
  normalizeFontPreset,
} from '../utils/fontPreferences';

function SettingsPage() {
  const [textSize, setTextSize] = useState(localStorage.getItem('textSize') || 'medium');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [fontFamily, setFontFamily] = useState(() =>
    normalizeFontPreset(localStorage.getItem('fontFamily'))
  );
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

    applyFontFamilyPreset(fontFamily);
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
            <section className="settings-hero">
              <img
                src={blobAccent}
                alt=""
                className="settings-hero-blob"
                aria-hidden="true"
              />
              <span className="section-index">[ 06 ] · PREFERENCES</span>
              <h1 className="settings-hero-title">
                YOUR<br />
                <span className="display-title--silver">CONSOLE.</span>
              </h1>
              <p className="settings-description">
                Tune the way ClockGuard looks and feels — every change saves
                instantly to this device.
              </p>
            </section>

            <div className="settings-section">
              <span className="section-index">[ 01 ] · TEXT</span>
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
              <span className="section-index">[ 02 ] · MODE</span>
              <h2>Theme</h2>
              <div className="setting-options">
                <button
                  className={`setting-option ${theme === 'light' ? 'active' : ''}`}
                  onClick={() => handleThemeChange('light')}
                >
                  Light Mode
                </button>
                <button
                  className={`setting-option ${theme === 'dark' ? 'active' : ''}`}
                  onClick={() => handleThemeChange('dark')}
                >
                  Dark Mode
                </button>
              </div>
            </div>

            <div className="settings-section">
              <span className="section-index">[ 03 ] · TYPE</span>
              <h2>Font Family</h2>
              <div className="setting-options">
                <button
                  type="button"
                  className={`setting-option ${fontFamily === FONT_PRESETS.NORMAL ? 'active' : ''}`}
                  onClick={() => handleFontChange(FONT_PRESETS.NORMAL)}
                >
                  Normal
                </button>
                <button
                  type="button"
                  className={`setting-option ${fontFamily === FONT_PRESETS.SERIF ? 'active' : ''}`}
                  onClick={() => handleFontChange(FONT_PRESETS.SERIF)}
                >
                  Serif
                </button>
                <button
                  type="button"
                  className={`setting-option ${fontFamily === FONT_PRESETS.ROUNDED ? 'active' : ''}`}
                  onClick={() => handleFontChange(FONT_PRESETS.ROUNDED)}
                >
                  Rounded
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
