/**
 * ClockGuard Theme Configuration
 * 
 * This file contains the core design tokens for the ClockGuard admin dashboard.
 * Color values are placeholders until the logo and brand identity are finalized.
 */

export const theme = {
  // Brand Identity
  brandName: "ClockGuard",
  
  // Colors - Based on ClockGuard logo (blue & teal)
  colors: {
    // Primary brand colors from logo
    primary: "#2B5F8D",      // Navy blue from logo
    primaryHover: "#234a6d",
    primaryLight: "#3a7ab0",
    
    // Accent color from logo
    accent: "#00B4D8",       // Teal/cyan from logo
    accentHover: "#0096b8",
    accentLight: "#33c4e2",
    
    // Backgrounds
    background: "#f8fafc",   // Subtle off-white
    backgroundAlt: "#f1f5f9",
    surface: "#ffffff",
    
    // Text colors
    text: "#1e293b",
    textSecondary: "#64748b",
    textLight: "#94a3b8",
    
    // Semantic colors
    success: "#10b981",
    warning: "#f59e0b",
    error: "#ef4444",
    info: "#00B4D8",         // Using brand teal
    
    // Borders
    border: "#e2e8f0",
    borderLight: "#f1f5f9",
    
    // Shadows
    shadow: "rgba(43, 95, 141, 0.08)",      // Subtle primary blue tint
    shadowDark: "rgba(43, 95, 141, 0.12)",
  },
  
  // Spacing scale (in pixels)
  spacing: {
    xs: "4px",
    sm: "8px",
    md: "16px",
    lg: "24px",
    xl: "32px",
    xxl: "48px",
  },
  
  // Border radius
  radius: {
    sm: "4px",
    md: "8px",
    lg: "12px",
    xl: "16px",
    full: "9999px",
  },
  
  // Shadows
  shadows: {
    sm: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
  },
  
  // Typography
  fonts: {
    body: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
    heading: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
    mono: "ui-monospace, Menlo, Monaco, 'Cascadia Mono', 'Segoe UI Mono', 'Roboto Mono', 'Oxygen Mono', 'Ubuntu Monospace', 'Source Code Pro', 'Fira Mono', 'Droid Sans Mono', 'Courier New', monospace",
  },
  
  // Font sizes
  fontSizes: {
    xs: "12px",
    sm: "14px",
    md: "16px",
    lg: "18px",
    xl: "20px",
    "2xl": "24px",
    "3xl": "30px",
    "4xl": "36px",
  },
  
  // Font weights
  fontWeights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  
  // Transitions
  transitions: {
    fast: "150ms ease-in-out",
    normal: "250ms ease-in-out",
    slow: "350ms ease-in-out",
  },
  
  // Breakpoints for responsive design
  breakpoints: {
    mobile: "640px",
    tablet: "768px",
    desktop: "1024px",
    wide: "1280px",
  },
};

export default theme;
