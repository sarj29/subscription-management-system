import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Package,
  Layers,
  FileText,
  Repeat,
  Receipt,
  CreditCard,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Zap,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Sidebar({ collapsed, onToggle }) {
  const { user, isCustomer } = useAuth();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard, public: true },
    { label: 'Subscriptions', path: '/subscriptions', icon: Repeat, public: true },
    { label: 'Invoices', path: '/invoices', icon: Receipt, public: true },
    { label: 'Quotations', path: '/quotations', icon: FileText, staffOnly: true },
    { label: 'Customers', path: '/customers', icon: Users, staffOnly: true },
    { label: 'Products', path: '/products', icon: Package, staffOnly: true },
    { label: 'Plans', path: '/plans', icon: Layers, staffOnly: true },
    { label: 'Payments', path: '/payments', icon: CreditCard, staffOnly: true },
    { label: 'Settings', path: '/settings', icon: Settings, public: true },
  ];

  const visibleItems = navItems.filter((item) => {
    if (isCustomer && item.staffOnly) return false;
    return true;
  });

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="brand-logo">
          <div className="brand-badge">
            <Zap size={20} />
          </div>
          {!collapsed && <span>Brightloop</span>}
        </div>
        <button
          className="btn-icon"
          onClick={onToggle}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className="sidebar-nav">
        {!collapsed && <div className="nav-section-title">Navigation</div>}
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={20} />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        {!collapsed ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: '50%',
                background: 'var(--primary-light)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 700,
                fontSize: '0.85rem',
              }}
            >
              {user?.full_name ? user.full_name.charAt(0) : 'U'}
            </div>
            <div style={{ overflow: 'hidden' }}>
              <p
                style={{
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  textOverflow: 'ellipsis',
                  overflow: 'hidden',
                }}
              >
                {user?.full_name || 'Demo User'}
              </p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                <Shield size={12} color="var(--primary)" />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                  {user?.role || 'Guest'}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <Shield size={20} color="var(--primary)" title={user?.role} />
        )}
      </div>
    </aside>
  );
}
