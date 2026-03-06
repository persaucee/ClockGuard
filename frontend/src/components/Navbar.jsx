/**
 * Navbar Component - ClockGuard Admin Dashboard
 * 
 * Reusable navigation bar with:
 * - ClockGuard logo on the left
 * - Logout button on the right (navigates to /login)
 * - Responsive design for mobile and desktop
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Navbar.css';
import clockGuardLogo from '../assets/CGlogo.png';

function Navbar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    console.log('Logout clicked');
    // Navigate back to login
    navigate('/login');
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
