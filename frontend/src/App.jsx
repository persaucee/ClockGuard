import React, { useEffect } from 'react';
import AppRouter from './routes/AppRouter';
import './styles/global.css';

function App() {
  useEffect(() => {
    const textSize = localStorage.getItem('textSize') || 'medium';
    const theme = localStorage.getItem('theme') || 'light';
    const fontFamily = localStorage.getItem('fontFamily') || 'system';

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
    }
    
    if (fontFamily === 'serif') {
      root.style.fontFamily = 'Georgia, Cambria, "Times New Roman", Times, serif';
    } else if (fontFamily === 'mono') {
      root.style.fontFamily = '"Courier New", Courier, monospace';
    } else {
      root.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif';
    }
  }, []);

  return <AppRouter />;
}

export default App;
