import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Building,
  Percent,
  Tag,
  User,
  CheckCircle2,
  Plus,
  Trash2,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('company');
  const [notice, setNotice] = useState('');

  // Company settings
  const [companySettings, setCompanySettings] = useState({
    companyName: 'Brightloop Technologies Inc.',
    taxId: 'US-884920199',
    billingEmail: 'billing@brightloop.com',
    currency: 'USD',
    defaultPaymentTerms: '14',
    invoicePrefix: 'INV-2026',
    address: '100 Montgomery St, Suite 1400, San Francisco, CA',
  });

  // Tax rates
  const [taxRates, setTaxRates] = useState([
    { id: 'tax-1', name: 'Standard VAT', rate: 18.0, country: 'EU / Global', is_default: true },
    { id: 'tax-2', name: 'California Sales Tax', rate: 8.25, country: 'US-CA', is_default: false },
    { id: 'tax-3', name: 'Zero-Rated B2B Export', rate: 0.0, country: 'International', is_default: false },
  ]);
  const [newTax, setNewTax] = useState({ name: '', rate: '', country: 'US' });

  // Discount codes
  const [discounts, setDiscounts] = useState([
    { id: 'disc-1', code: 'WELCOME10', percent: 10, description: 'New subscriber welcome discount' },
    { id: 'disc-2', code: 'ANNUAL20', percent: 20, description: 'Annual commitment incentive' },
    { id: 'disc-3', code: 'PARTNER30', percent: 30, description: 'Certified reseller partner margin' },
  ]);
  const [newDiscount, setNewDiscount] = useState({ code: '', percent: '', description: '' });

  const showNotice = (msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(''), 4000);
  };

  const handleSaveCompany = (e) => {
    e.preventDefault();
    showNotice('Billing & company preferences updated successfully.');
  };

  const handleAddTax = (e) => {
    e.preventDefault();
    if (!newTax.name || !newTax.rate) return;
    setTaxRates((prev) => [
      ...prev,
      {
        id: `tax-${Date.now()}`,
        name: newTax.name,
        rate: parseFloat(newTax.rate) || 0,
        country: newTax.country,
        is_default: false,
      },
    ]);
    setNewTax({ name: '', rate: '', country: 'US' });
    showNotice('Tax rate added.');
  };

  const handleDeleteTax = (id) => {
    setTaxRates((prev) => prev.filter((t) => t.id !== id));
    showNotice('Tax rate removed.');
  };

  const handleAddDiscount = (e) => {
    e.preventDefault();
    if (!newDiscount.code || !newDiscount.percent) return;
    setDiscounts((prev) => [
      ...prev,
      {
        id: `disc-${Date.now()}`,
        code: newDiscount.code.toUpperCase(),
        percent: parseFloat(newDiscount.percent) || 0,
        description: newDiscount.description || 'Promotional discount',
      },
    ]);
    setNewDiscount({ code: '', percent: '', description: '' });
    showNotice('Discount rule created.');
  };

  const handleDeleteDiscount = (id) => {
    setDiscounts((prev) => prev.filter((d) => d.id !== id));
    showNotice('Discount removed.');
  };

  const tabs = [
    { id: 'company', label: 'Company & Billing', icon: Building },
    { id: 'taxes', label: 'Taxes & Compliance', icon: Percent },
    { id: 'discounts', label: 'Discounts & Codes', icon: Tag },
    { id: 'account', label: 'Account & Security', icon: User },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Platform Settings</h1>
          <p className="page-subtitle">
            Configure system billing rules, corporate identifiers, tax matrices and promotional campaigns.
          </p>
        </div>
      </div>

      {notice && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: 'var(--primary-light)',
            color: 'var(--primary)',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
            fontSize: '0.875rem',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <CheckCircle2 size={16} /> {notice}
        </div>
      )}

      {/* Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid var(--border)',
          marginBottom: '1.5rem',
          overflowX: 'auto',
        }}
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1rem',
                fontSize: '0.9rem',
                fontWeight: 600,
                color: isActive ? 'var(--primary)' : 'var(--text-secondary)',
                borderBottom: isActive ? '2px solid var(--primary)' : '2px solid transparent',
                marginBottom: -1,
                background: 'none',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Company & Billing */}
      {activeTab === 'company' && (
        <div className="card-table" style={{ padding: '1.75rem', maxWidth: 760 }}>
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1.25rem' }}>Company Information & Invoice Terms</h3>
          <form onSubmit={handleSaveCompany} style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Legal Company Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={companySettings.companyName}
                  onChange={(e) => setCompanySettings({ ...companySettings, companyName: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Tax ID / VAT Registration #</label>
                <input
                  type="text"
                  className="form-input"
                  value={companySettings.taxId}
                  onChange={(e) => setCompanySettings({ ...companySettings, taxId: e.target.value })}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Billing Notifications Email</label>
                <input
                  type="email"
                  className="form-input"
                  value={companySettings.billingEmail}
                  onChange={(e) => setCompanySettings({ ...companySettings, billingEmail: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Base Currency</label>
                <select
                  className="form-select"
                  value={companySettings.currency}
                  onChange={(e) => setCompanySettings({ ...companySettings, currency: e.target.value })}
                >
                  <option value="USD">USD ($) — United States Dollar</option>
                  <option value="EUR">EUR (€) — Euro</option>
                  <option value="GBP">GBP (£) — British Pound</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Default Payment Due Days</label>
                <input
                  type="number"
                  className="form-input"
                  value={companySettings.defaultPaymentTerms}
                  onChange={(e) => setCompanySettings({ ...companySettings, defaultPaymentTerms: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Invoice Number Prefix</label>
                <input
                  type="text"
                  className="form-input"
                  value={companySettings.invoicePrefix}
                  onChange={(e) => setCompanySettings({ ...companySettings, invoicePrefix: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Registered Office Address</label>
              <textarea
                className="form-textarea"
                rows={2}
                value={companySettings.address}
                onChange={(e) => setCompanySettings({ ...companySettings, address: e.target.value })}
              />
            </div>

            {isAdmin && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
                <button type="submit" className="btn btn-primary">
                  Save Changes
                </button>
              </div>
            )}
          </form>
        </div>
      )}

      {/* Tab 2: Taxes */}
      {activeTab === 'taxes' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: 840 }}>
          <div className="card-table" style={{ margin: 0 }}>
            <div className="table-toolbar">
              <h3 style={{ fontSize: '1.05rem' }}>Configured Tax Jurisdictions</h3>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Tax Name</th>
                  <th>Region / Country</th>
                  <th>Rate (%)</th>
                  <th>Default</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {taxRates.map((t) => (
                  <tr key={t.id}>
                    <td style={{ fontWeight: 600 }}>{t.name}</td>
                    <td>{t.country}</td>
                    <td style={{ fontWeight: 600 }}>{t.rate.toFixed(2)}%</td>
                    <td>
                      {t.is_default ? (
                        <span className="badge badge-active">Default</span>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>Optional</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {isAdmin && (
                        <button
                          className="btn-icon"
                          onClick={() => handleDeleteTax(t.id)}
                          style={{ color: 'var(--danger)' }}
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {isAdmin && (
            <div className="card-table" style={{ padding: '1.25rem', margin: 0 }}>
              <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>Add New Tax Rate</h4>
              <form onSubmit={handleAddTax} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '0.75rem', alignItems: 'flex-end' }}>
                <div className="form-group">
                  <label className="form-label">Tax Rule Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. State Sales Tax"
                    value={newTax.name}
                    onChange={(e) => setNewTax({ ...newTax, name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Rate (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-input"
                    placeholder="e.g. 8.5"
                    value={newTax.rate}
                    onChange={(e) => setNewTax({ ...newTax, rate: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Region</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="US / EU"
                    value={newTax.country}
                    onChange={(e) => setNewTax({ ...newTax, country: e.target.value })}
                  />
                </div>
                <button type="submit" className="btn btn-primary" style={{ height: 38 }}>
                  <Plus size={15} /> Add
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: Discounts */}
      {activeTab === 'discounts' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxWidth: 840 }}>
          <div className="card-table" style={{ margin: 0 }}>
            <div className="table-toolbar">
              <h3 style={{ fontSize: '1.05rem' }}>Promotional & Partner Discounts</h3>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Promo Code</th>
                  <th>Discount %</th>
                  <th>Description</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {discounts.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <span
                        style={{
                          fontFamily: 'monospace',
                          fontWeight: 700,
                          background: 'var(--bg-subtle)',
                          padding: '0.2rem 0.5rem',
                          borderRadius: 'var(--radius-sm)',
                        }}
                      >
                        {d.code}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: 'var(--primary)' }}>{d.percent}% OFF</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{d.description}</td>
                    <td style={{ textAlign: 'right' }}>
                      {isAdmin && (
                        <button
                          className="btn-icon"
                          onClick={() => handleDeleteDiscount(d.id)}
                          style={{ color: 'var(--danger)' }}
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {isAdmin && (
            <div className="card-table" style={{ padding: '1.25rem', margin: 0 }}>
              <h4 style={{ fontSize: '0.95rem', marginBottom: '0.75rem' }}>Create Discount Rule</h4>
              <form onSubmit={handleAddDiscount} style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 2.5fr auto', gap: '0.75rem', alignItems: 'flex-end' }}>
                <div className="form-group">
                  <label className="form-label">Code</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="PROMOCODE"
                    value={newDiscount.code}
                    onChange={(e) => setNewDiscount({ ...newDiscount, code: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Discount %</label>
                  <input
                    type="number"
                    step="0.1"
                    max="100"
                    min="1"
                    className="form-input"
                    placeholder="15"
                    value={newDiscount.percent}
                    onChange={(e) => setNewDiscount({ ...newDiscount, percent: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Short description"
                    value={newDiscount.description}
                    onChange={(e) => setNewDiscount({ ...newDiscount, description: e.target.value })}
                  />
                </div>
                <button type="submit" className="btn btn-primary" style={{ height: 38 }}>
                  <Plus size={15} /> Add
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Account */}
      {activeTab === 'account' && (
        <div className="card-table" style={{ padding: '1.75rem', maxWidth: 640 }}>
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1.25rem' }}>Signed-in Identity</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input type="text" className="form-input" value={user?.full_name || 'Admin User'} readOnly />
            </div>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input type="email" className="form-input" value={user?.email || 'admin@brightloop.com'} readOnly />
            </div>
            <div className="form-group">
              <label className="form-label">Access Role</label>
              <div>
                <span className="badge badge-confirmed" style={{ textTransform: 'uppercase' }}>
                  {user?.role || 'admin'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

