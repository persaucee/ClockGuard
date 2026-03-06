/**
 * SettingsPage - Placeholder (Scrum 11)
 * 
 * Features:
 * - Navbar on top
 * - Sidebar navigation
 * - Content area with placeholder text
 */

import React from 'react';
import './SettingsPage.css';
import Navbar from '../components/Navbar';
import Sidebar from '../components/Sidebar';

function SettingsPage() {
  return (
    <div className="settings-page">
      <Navbar />
      <div className="page-layout">
        <Sidebar />
        <main className="page-content">
          <div className="content-container">
            <h1>Settings</h1>
            <p>Content coming in Sprint 2</p>
          </div>
        </main>
      </div>
    </div>
  );
}

export default SettingsPage;
