import React, { useState, useEffect } from 'react';
import { Sun, Moon, LogOut, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const { user, loginAs, logout } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="top-navbar">
      <div className="nav-left">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="status-dot dot-online" title="System operational" />
          <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)', fontWeight: 500 }}>
            Brightloop Cloud Engine • v1.0.0
          </span>
        </div>
      </div>

      <div className="nav-right">
        {/* Quick Demo Role Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'var(--bg-subtle)', padding: '0.25rem 0.5rem', borderRadius: 'var(--radius-full)' }}>
          <UserCheck size={14} color="var(--primary)" />
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Role:</span>
          <select
            style={{
              border: 'none',
              background: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              color: 'var(--primary)',
              cursor: 'pointer',
              outline: 'none',
            }}
            value={user?.role || 'admin'}
            onChange={(e) => loginAs(e.target.value)}
          >
            <option value="admin">Admin</option>
            <option value="staff">Staff</option>
            <option value="customer">Customer</option>
          </select>
        </div>

        {/* Theme Switcher */}
        <button
          className="btn-icon"
          onClick={toggleTheme}
          title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} theme`}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>

        {/* Logout */}
        <button
          className="btn-icon"
          onClick={handleLogout}
          title="Sign out"
          style={{ color: 'var(--danger)' }}
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
