import React, { useState, useEffect } from 'react';
import './SettingsPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';
import blobAccent from '../assets/Images/Blob.png';

function SettingsPage() {
  const [textSize, setTextSize] = useState(localStorage.getItem('textSize') || 'medium');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');

  useEffect(() => {
    applyPreferences();
  }, [textSize, theme]);

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
  };

  const handleTextSizeChange = (size) => {
    setTextSize(size);
    localStorage.setItem('textSize', size);
  };

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
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
          </div>
        </main>
      </div>
    </div>
  );
}

export default SettingsPage;
