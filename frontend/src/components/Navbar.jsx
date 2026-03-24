import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Navbar.css';
import clockGuardLogo from '../assets/CGlogo.png';

function Navbar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    console.log('Logout clicked');
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
          <img src={clockGuardLogo} alt="ClockGuard Logo" />
          <span className="navbar-brand">ClockGuard</span>
        </div>

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
