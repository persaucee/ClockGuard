import React, { useEffect } from 'react';
import AppRouter from './routes/AppRouter';
import { applyFontFamilyPreset, normalizeFontPreset } from './utils/fontPreferences';
import './index.css';
import './styles/global.css';
import './App.css';

function App() {
  useEffect(() => {
    const textSize = localStorage.getItem('textSize') || 'medium';
    const theme = localStorage.getItem('theme') || 'light';
    const fontPreset = normalizeFontPreset(localStorage.getItem('fontFamily'));

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

    applyFontFamilyPreset(fontPreset);
  }, []);

  return <AppRouter />;
}

export default App;
