/**
 * Navbar Component - ClockGuard Admin Dashboard
 * 
 * Reusable navigation bar with:
 * - ClockGuard logo on the left
 * - Logout button on the right
 * - Responsive design for mobile and desktop
 */

import React from 'react';
import './Navbar.css';
import clockGuardLogo from '../assets/CGlogo.png';

function Navbar() {
  const handleLogout = () => {
    // Placeholder - will be implemented in Scrum 10 with auth logic
    console.log('Logout clicked');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo Section */}
        <div className="navbar-logo">
          <img src={clockGuardLogo} alt="ClockGuard Logo" />
          <span className="navbar-brand">ClockGuard</span>
        </div>

        {/* Actions Section */}
        <div className="navbar-actions">
          <button className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
