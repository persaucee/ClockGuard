import React, { useState, useEffect } from 'react';
import './SettingsPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

function SettingsPage() {
  const [textSize, setTextSize] = useState(localStorage.getItem('textSize') || 'medium');
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'light');
  const [fontFamily, setFontFamily] = useState(localStorage.getItem('fontFamily') || 'system');

  useEffect(() => {
    applyPreferences();
  }, [textSize, theme, fontFamily]);

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
          </div>
        </main>
      </div>
    </div>
  );
}

export default SettingsPage;
