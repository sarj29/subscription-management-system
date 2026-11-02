import React, { useState, useEffect } from 'react';
import {
  Plus,
  Repeat,
  Eye,
  Pause,
  Play,
  RotateCw,
  XCircle,
  Receipt,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { subscriptionService } from '../services/subscriptionService';
import { customerService } from '../services/customerService';
import { planService } from '../services/planService';
import { useAuth } from '../context/AuthContext';

export default function Subscriptions() {
  const { isCustomer } = useAuth();
  const [subscriptions, setSubscriptions] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedSub, setSelectedSub] = useState(null);
  const [actionNotice, setActionNotice] = useState('');

  // New Subscription Form
  const [form, setForm] = useState({
    customer_id: '',
    plan_id: '',
    start_date: new Date().toISOString().split('T')[0],
    notes: '',
    currency: 'USD',
    lines: [
      {
        description: 'Primary Plan Seat',
        quantity: 1,
        unit_price: 100,
        discount_percent: 0,
        tax_percent: 10,
      },
    ],
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [subsData, custsData, plansData] = await Promise.all([
        subscriptionService.list(),
        customerService.list(),
        planService.list(),
      ]);
      setSubscriptions(subsData);
      setCustomers(custsData);
      setPlans(plansData);

      if (custsData.length > 0 && !form.customer_id) {
        setForm((prev) => ({
          ...prev,
          customer_id: custsData[0].id,
          plan_id: plansData[0]?.id || '',
        }));
      }
    } catch (err) {
      console.error('Failed to load subscriptions data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showNotice = (msg) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(''), 4000);
  };

  const handleOpenCreate = () => {
    setForm({
      customer_id: customers[0]?.id || '',
      plan_id: plans[0]?.id || '',
      start_date: new Date().toISOString().split('T')[0],
      notes: '',
      currency: 'USD',
      lines: [
        {
          description: plans[0]?.name ? `${plans[0].name} Subscription` : 'Service Tier',
          quantity: 1,
          unit_price: Number(plans[0]?.base_price) || 99,
          discount_percent: 0,
          tax_percent: 10,
        },
      ],
    });
    setIsCreateOpen(true);
  };

  const handleAddLine = () => {
    setForm((prev) => ({
      ...prev,
      lines: [
        ...prev.lines,
        {
          description: 'Add-on License / Seat',
          quantity: 1,
          unit_price: 50,
          discount_percent: 0,
          tax_percent: 10,
        },
      ],
    }));
  };

  const handleRemoveLine = (idx) => {
    setForm((prev) => ({
      ...prev,
      lines: prev.lines.filter((_, i) => i !== idx),
    }));
  };

  const handleLineChange = (idx, field, val) => {
    setForm((prev) => {
      const updatedLines = [...prev.lines];
      updatedLines[idx] = { ...updatedLines[idx], [field]: val };
      return { ...prev, lines: updatedLines };
    });
  };

  const calculateTotals = () => {
    const subtotal = form.lines.reduce((acc, l) => {
      const lineBase = Number(l.quantity || 0) * Number(l.unit_price || 0);
      return acc + lineBase * (1 - (Number(l.discount_percent || 0) / 100));
    }, 0);

    const taxAmount = form.lines.reduce((acc, l) => {
      const lineBase = Number(l.quantity || 0) * Number(l.unit_price || 0);
      const lineSub = lineBase * (1 - (Number(l.discount_percent || 0) / 100));
      return acc + lineSub * (Number(l.tax_percent || 0) / 100);
    }, 0);

    return {
      subtotal: Number(subtotal.toFixed(2)),
      taxAmount: Number(taxAmount.toFixed(2)),
      total: Number((subtotal + taxAmount).toFixed(2)),
    };
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    try {
      const selCust = customers.find((c) => c.id === form.customer_id);
      const selPlan = plans.find((p) => p.id === form.plan_id);

      await subscriptionService.create({
        ...form,
        customer_name: selCust?.company_name || 'Client',
        plan_name: selPlan?.name || 'Default Plan',
        status: 'active',
      });

      setIsCreateOpen(false);
      showNotice('Subscription created successfully.');
      loadData();
    } catch (err) {
      alert(err.message || 'Error creating subscription');
    }
  };

  const handlePause = async (sub) => {
    try {
      await subscriptionService.pause(sub.id);
      showNotice(`Subscription ${sub.reference} paused.`);
      loadData();
      if (selectedSub?.id === sub.id) {
        setSelectedSub((prev) => ({ ...prev, status: 'paused' }));
      }
    } catch (err) {
      alert(err.message || 'Failed to pause subscription');
    }
  };

  const handleResume = async (sub) => {
    try {
      await subscriptionService.resume(sub.id);
      showNotice(`Subscription ${sub.reference} resumed to active.`);
      loadData();
      if (selectedSub?.id === sub.id) {
        setSelectedSub((prev) => ({ ...prev, status: 'active' }));
      }
    } catch (err) {
      alert(err.message || 'Failed to resume subscription');
    }
  };

  const handleClose = async (sub) => {
    if (!window.confirm(`Are you sure you want to terminate subscription ${sub.reference}?`)) return;
    try {
      await subscriptionService.close(sub.id, 'Customer termination request');
      showNotice(`Subscription ${sub.reference} has been closed.`);
      loadData();
      if (selectedSub?.id === sub.id) {
        setSelectedSub((prev) => ({ ...prev, status: 'closed' }));
      }
    } catch (err) {
      alert(err.message || 'Failed to close subscription');
    }
  };

  const handleRenew = async (sub) => {
    try {
      const renewed = await subscriptionService.renew(sub.id);
      showNotice(`Subscription ${sub.reference} renewed for next cycle.`);
      loadData();
      if (selectedSub?.id === sub.id) {
        setSelectedSub(renewed);
      }
    } catch (err) {
      alert(err.message || 'Failed to renew subscription');
    }
  };

  const handleGenerateInvoice = async (sub) => {
    try {
      const inv = await subscriptionService.generateInvoice(sub.id);
      showNotice(`Draft invoice ${inv.invoice_number || 'created'} generated successfully.`);
    } catch (err) {
      alert(err.message || 'Failed to generate invoice');
    }
  };

  const columns = [
    {
      header: 'Reference & Plan',
      accessor: 'reference',
      render: (row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.reference}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {row.plan_name || 'Standard Tier'}
          </div>
        </div>
      ),
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
      render: (row) => (
        <span style={{ fontWeight: 500 }}>{row.customer_name || 'Acme Client'}</span>
      ),
    },
    {
      header: 'Cycle Amount',
      accessor: 'total_amount',
      render: (row) => (
        <span style={{ fontWeight: 600 }}>${Number(row.total_amount || 0).toFixed(2)}</span>
      ),
    },
    {
      header: 'Next Billing',
      accessor: 'next_billing_date',
      render: (row) => (
        <span style={{ fontSize: '0.875rem' }}>{row.next_billing_date || 'N/A'}</span>
      ),
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      align: 'right',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.4rem' }}>
          <button
            className="btn-icon"
            onClick={() => {
              setSelectedSub(row);
              setIsDetailOpen(true);
            }}
            title="View Details"
          >
            <Eye size={16} />
          </button>
          {!isCustomer && (
            <>
              {row.status === 'active' && (
                <button
                  className="btn-icon"
                  onClick={() => handlePause(row)}
                  title="Pause Subscription"
                  style={{ color: 'var(--warning)' }}
                >
                  <Pause size={15} />
                </button>
              )}
              {row.status === 'paused' && (
                <button
                  className="btn-icon"
                  onClick={() => handleResume(row)}
                  title="Resume Subscription"
                  style={{ color: 'var(--success)' }}
                >
                  <Play size={15} />
                </button>
              )}
              {['active', 'paused'].includes(row.status) && (
                <button
                  className="btn-icon"
                  onClick={() => handleGenerateInvoice(row)}
                  title="Generate Invoice Now"
                  style={{ color: 'var(--primary)' }}
                >
                  <Receipt size={15} />
                </button>
              )}
            </>
          )}
        </div>
      ),
    },
  ];

  const filterOptions = [
    { label: 'Active', value: 'active' },
    { label: 'Paused', value: 'paused' },
    { label: 'Confirmed', value: 'confirmed' },
    { label: 'Draft', value: 'draft' },
    { label: 'Closed', value: 'closed' },
  ];

  const totals = calculateTotals();

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Subscriptions</h1>
          <p className="page-subtitle">
            Manage recurring customer accounts, billing frequencies and contract lifecycles.
          </p>
        </div>
        {!isCustomer && (
          <div className="header-actions">
            <button className="btn btn-primary" onClick={handleOpenCreate}>
              <Plus size={16} /> New Subscription
            </button>
          </div>
        )}
      </div>

      {actionNotice && (
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
          <CheckCircle2 size={16} /> {actionNotice}
        </div>
      )}

      <DataTable
        columns={columns}
        data={subscriptions}
        loading={loading}
        searchPlaceholder="Search reference, customer or plan..."
        searchField="reference"
        filterKey="status"
        filterOptions={filterOptions}
        emptyMessage="No subscriptions match your search"
      />

      {/* Subscription Detail Modal */}
      <Modal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        title={selectedSub ? `Subscription: ${selectedSub.reference}` : 'Subscription Details'}
        maxWidth="680px"
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {!isCustomer && selectedSub && selectedSub.status === 'active' && (
                <button className="btn btn-secondary" onClick={() => handlePause(selectedSub)}>
                  <Pause size={14} /> Pause
                </button>
              )}
              {!isCustomer && selectedSub && selectedSub.status === 'paused' && (
                <button className="btn btn-secondary" onClick={() => handleResume(selectedSub)}>
                  <Play size={14} /> Resume
                </button>
              )}
              {!isCustomer && selectedSub && ['active', 'paused'].includes(selectedSub.status) && (
                <button className="btn btn-secondary" onClick={() => handleRenew(selectedSub)}>
                  <RotateCw size={14} /> Renew Cycle
                </button>
              )}
              {!isCustomer && selectedSub && selectedSub.status !== 'closed' && (
                <button className="btn btn-danger-outline" onClick={() => handleClose(selectedSub)}>
                  <XCircle size={14} /> Terminate
                </button>
              )}
            </div>
            <button className="btn btn-secondary" onClick={() => setIsDetailOpen(false)}>
              Close
            </button>
          </div>
        }
      >
        {selectedSub && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                gap: '1rem',
                background: 'var(--bg-subtle)',
                padding: '1rem',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div>
                <span className="form-label">Customer</span>
                <p style={{ fontWeight: 600 }}>{selectedSub.customer_name || 'N/A'}</p>
              </div>
              <div>
                <span className="form-label">Current Status</span>
                <div>
                  <StatusBadge status={selectedSub.status} />
                </div>
              </div>
              <div>
                <span className="form-label">Next Billing Date</span>
                <p style={{ fontWeight: 600 }}>{selectedSub.next_billing_date || 'N/A'}</p>
              </div>
              <div>
                <span className="form-label">Total Amount</span>
                <p style={{ fontWeight: 700, color: 'var(--primary)', fontSize: '1.1rem' }}>
                  ${Number(selectedSub.total_amount || 0).toFixed(2)} {selectedSub.currency || 'USD'}
                </p>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.95rem', marginBottom: '0.6rem', color: 'var(--text-secondary)' }}>
                Subscription Line Items
              </h4>
              <table className="data-table" style={{ border: '1px solid var(--border)' }}>
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Price</th>
                    <th>Tax %</th>
                    <th style={{ textAlign: 'right' }}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedSub.lines || []).map((line, idx) => {
                    const lineSub = Number(line.quantity || 1) * Number(line.unit_price || 0) * (1 - (Number(line.discount_percent || 0) / 100));
                    const lineTot = lineSub * (1 + (Number(line.tax_percent || 0) / 100));
                    return (
                      <tr key={idx}>
                        <td>{line.description}</td>
                        <td>{line.quantity}</td>
                        <td>${Number(line.unit_price).toFixed(2)}</td>
                        <td>{line.tax_percent || 0}%</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>${lineTot.toFixed(2)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {!isCustomer && ['active', 'paused'].includes(selectedSub.status) && (
              <div
                style={{
                  borderTop: '1px solid var(--border)',
                  paddingTop: '1rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <p style={{ fontSize: '0.875rem', fontWeight: 600 }}>Recurring Billing Integration</p>
                  <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                    Trigger draft invoice generation immediately for this subscriber cycle.
                  </p>
                </div>
                <button className="btn btn-primary" onClick={() => handleGenerateInvoice(selectedSub)}>
                  <Receipt size={15} /> Bill Customer
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Create Subscription Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Subscription"
        maxWidth="680px"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleCreateSubmit}>
              Create Subscription
            </button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Customer</label>
              <select
                className="form-select"
                value={form.customer_id}
                onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
                required
              >
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.company_name} ({c.contact_name})
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Subscription Plan</label>
              <select
                className="form-select"
                value={form.plan_id}
                onChange={(e) => {
                  const sel = plans.find((p) => p.id === e.target.value);
                  setForm({
                    ...form,
                    plan_id: e.target.value,
                    lines: [
                      {
                        description: sel ? `${sel.name} Plan` : 'Primary Service',
                        quantity: 1,
                        unit_price: Number(sel?.base_price || 99),
                        discount_percent: 0,
                        tax_percent: 10,
                      },
                    ],
                  });
                }}
                required
              >
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} — ${Number(p.base_price).toFixed(2)} ({p.billing_interval})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Start Date</label>
              <input
                type="date"
                className="form-input"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Currency</label>
              <select
                className="form-select"
                value={form.currency}
                onChange={(e) => setForm({ ...form, currency: e.target.value })}
              >
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
              </select>
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <label className="form-label">Line Items</label>
              <button
                type="button"
                className="btn btn-outline"
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}
                onClick={handleAddLine}
              >
                <Plus size={13} /> Add Line
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {form.lines.map((line, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '2fr 1fr 1fr 1fr auto',
                    gap: '0.5rem',
                    alignItems: 'center',
                    background: 'var(--bg-subtle)',
                    padding: '0.5rem',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Description"
                    value={line.description}
                    onChange={(e) => handleLineChange(idx, 'description', e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    className="form-input"
                    placeholder="Qty"
                    min="1"
                    value={line.quantity}
                    onChange={(e) => handleLineChange(idx, 'quantity', e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    step="0.01"
                    className="form-input"
                    placeholder="Price"
                    value={line.unit_price}
                    onChange={(e) => handleLineChange(idx, 'unit_price', e.target.value)}
                    required
                  />
                  <input
                    type="number"
                    className="form-input"
                    placeholder="Tax %"
                    value={line.tax_percent}
                    onChange={(e) => handleLineChange(idx, 'tax_percent', e.target.value)}
                  />
                  {form.lines.length > 1 && (
                    <button
                      type="button"
                      className="btn-icon"
                      onClick={() => handleRemoveLine(idx)}
                      style={{ color: 'var(--danger)', width: 30, height: 30 }}
                      title="Remove"
                    >
                      <XCircle size={15} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div
            style={{
              padding: '0.75rem 1rem',
              background: 'var(--bg-subtle)',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Subtotal: ${totals.subtotal.toFixed(2)} | Tax: ${totals.taxAmount.toFixed(2)}
            </span>
            <span style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--primary)' }}>
              Cycle Total: ${totals.total.toFixed(2)} {form.currency}
            </span>
          </div>
        </form>
      </Modal>
    </div>
  );
}

