import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const SIDEBAR_STORAGE_KEY = 'cg-sidebar-open';

function Sidebar() {
  const [isOpen, setIsOpen] = useState(() => {
    if (typeof window === 'undefined') return true;
    const saved = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
    return saved === null ? true : saved === 'true';
  });

  useEffect(() => {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(isOpen));
  }, [isOpen]);

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '01' },
    { path: '/employees', label: 'Employees', icon: '02' },
    { path: '/attendance-logs', label: 'Attendance', icon: '03' },
    { path: '/settings', label: 'Settings', icon: '04' }
  ];

  return (
    <div className={`sidebar-shell${isOpen ? '' : ' sidebar-shell--closed'}`}>
      <aside className="sidebar" aria-hidden={!isOpen}>
        <div className="sidebar-inner">
          <nav className="sidebar-nav">
            <ul className="sidebar-menu">
              {navItems.map((item) => (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={({ isActive }) =>
                      isActive ? 'sidebar-link active' : 'sidebar-link'
                    }
                    tabIndex={isOpen ? 0 : -1}
                  >
                    <span className="sidebar-icon">{item.icon}</span>
                    <span className="sidebar-label">{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </aside>
      <button
        type="button"
        className="sidebar-toggle"
        onClick={() => setIsOpen((open) => !open)}
        aria-label={isOpen ? 'Collapse navigation' : 'Expand navigation'}
        aria-expanded={isOpen}
      >
        <span className="sidebar-toggle__chevron" aria-hidden="true">
          ›
        </span>
      </button>
    </div>
  );
}

export default Sidebar;
