import React, { useState, useEffect } from 'react';
import {
  Plus,
  FileText,
  Eye,
  Send,
  CheckCircle,
  XCircle,
  Repeat,
  Printer,
  CheckCircle2,
} from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { quotationService } from '../services/quotationService';
import { customerService } from '../services/customerService';
import { planService } from '../services/planService';
import { useAuth } from '../context/AuthContext';

export default function Quotations() {
  const { isCustomer } = useAuth();
  const [quotations, setQuotations] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isConvertOpen, setIsConvertOpen] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [notice, setNotice] = useState('');

  // Form
  const defaultDueDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().split('T')[0];
  };

  const [form, setForm] = useState({
    customer_id: '',
    valid_until: defaultDueDate(),
    currency: 'USD',
    notes: 'Net 30 days payment terms upon acceptance.',
    lines: [
      {
        description: 'Enterprise Cloud Instance',
        quantity: 1,
        unit_price: 299,
        discount_percent: 0,
        tax_percent: 10,
      },
    ],
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [quotesData, custsData, plansData] = await Promise.all([
        quotationService.list(),
        customerService.list(),
        planService.list(),
      ]);
      setQuotations(quotesData);
      setCustomers(custsData);
      setPlans(plansData);

      if (custsData.length > 0 && !form.customer_id) {
        setForm((prev) => ({ ...prev, customer_id: custsData[0].id }));
      }
      if (plansData.length > 0 && !selectedPlanId) {
        setSelectedPlanId(plansData[0].id);
      }
    } catch (err) {
      console.error('Failed to load quotations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showNotice = (msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(''), 4000);
  };

  const handleOpenCreate = () => {
    setForm({
      customer_id: customers[0]?.id || '',
      valid_until: defaultDueDate(),
      currency: 'USD',
      notes: 'Net 30 days payment terms upon acceptance.',
      lines: [
        {
          description: 'Brightloop Business Suite License',
          quantity: 1,
          unit_price: 199,
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
          description: 'Add-on Module / Feature',
          quantity: 1,
          unit_price: 49,
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
      await quotationService.create({
        ...form,
        customer_name: selCust?.company_name || 'Client',
      });
      setIsCreateOpen(false);
      showNotice('Quotation created as draft.');
      loadData();
    } catch (err) {
      alert(err.message || 'Error creating quotation');
    }
  };

  const handleStatusChange = async (quote, newStatus) => {
    try {
      await quotationService.updateStatus(quote.id, newStatus);
      showNotice(`Quotation status changed to ${newStatus}.`);
      loadData();
      if (selectedQuote?.id === quote.id) {
        setSelectedQuote((prev) => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      alert(err.message || 'Error updating quotation status');
    }
  };

  const handleOpenConvert = (quote) => {
    setSelectedQuote(quote);
    setSelectedPlanId(plans[0]?.id || '');
    setIsConvertOpen(true);
  };

  const handleConvertSubmit = async (e) => {
    e.preventDefault();
    if (!selectedQuote || !selectedPlanId) return;
    try {
      await quotationService.convertToSubscription(selectedQuote.id, selectedPlanId);
      setIsConvertOpen(false);
      showNotice(`Quotation converted to subscription successfully.`);
      loadData();
    } catch (err) {
      alert(err.message || 'Error converting quotation');
    }
  };

  const columns = [
    {
      header: 'Reference',
      accessor: 'reference',
      render: (row) => (
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.reference}</span>
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
      header: 'Valid Until',
      accessor: 'valid_until',
      render: (row) => (
        <span style={{ fontSize: '0.875rem' }}>{row.valid_until || 'N/A'}</span>
      ),
    },
    {
      header: 'Total Amount',
      accessor: 'total_amount',
      render: (row) => (
        <span style={{ fontWeight: 600 }}>${Number(row.total_amount || 0).toFixed(2)}</span>
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
              setSelectedQuote(row);
              setIsPreviewOpen(true);
            }}
            title="Preview Quotation"
          >
            <Eye size={16} />
          </button>
          {!isCustomer && (
            <>
              {row.status === 'draft' && (
                <button
                  className="btn-icon"
                  onClick={() => handleStatusChange(row, 'quotation')}
                  title="Send to Client"
                  style={{ color: 'var(--primary)' }}
                >
                  <Send size={15} />
                </button>
              )}
              {row.status === 'quotation' && (
                <>
                  <button
                    className="btn-icon"
                    onClick={() => handleStatusChange(row, 'confirmed')}
                    title="Confirm Acceptance"
                    style={{ color: 'var(--success)' }}
                  >
                    <CheckCircle size={15} />
                  </button>
                  <button
                    className="btn-icon"
                    onClick={() => handleStatusChange(row, 'cancelled')}
                    title="Cancel Quotation"
                    style={{ color: 'var(--danger)' }}
                  >
                    <XCircle size={15} />
                  </button>
                </>
              )}
              {row.status === 'confirmed' && (
                <button
                  className="btn btn-outline"
                  style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
                  onClick={() => handleOpenConvert(row)}
                  title="Convert to Recurring Subscription"
                >
                  <Repeat size={13} /> Subscribe
                </button>
              )}
            </>
          )}
        </div>
      ),
    },
  ];

  const filterOptions = [
    { label: 'Draft', value: 'draft' },
    { label: 'Quotation (Sent)', value: 'quotation' },
    { label: 'Confirmed', value: 'confirmed' },
    { label: 'Cancelled', value: 'cancelled' },
  ];

  const totals = calculateTotals();

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Quotations</h1>
          <p className="page-subtitle">
            Prepare, approve and convert customer pricing estimates into active recurring plans.
          </p>
        </div>
        {!isCustomer && (
          <div className="header-actions">
            <button className="btn btn-primary" onClick={handleOpenCreate}>
              <Plus size={16} /> New Quotation
            </button>
          </div>
        )}
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

      <DataTable
        columns={columns}
        data={quotations}
        loading={loading}
        searchPlaceholder="Search reference or customer..."
        searchField="reference"
        filterKey="status"
        filterOptions={filterOptions}
        emptyMessage="No quotations found"
      />

      {/* Convert to Subscription Modal */}
      <Modal
        isOpen={isConvertOpen}
        onClose={() => setIsConvertOpen(false)}
        title="Convert Quotation to Subscription"
        maxWidth="520px"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsConvertOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleConvertSubmit}>
              Confirm & Activate
            </button>
          </>
        }
      >
        <form onSubmit={handleConvertSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Converting quotation <strong>{selectedQuote?.reference}</strong> for{' '}
            <strong>{selectedQuote?.customer_name}</strong> into an active subscription.
          </p>

          <div className="form-group">
            <label className="form-label">Associate Subscription Plan</label>
            <select
              className="form-select"
              value={selectedPlanId}
              onChange={(e) => setSelectedPlanId(e.target.value)}
              required
            >
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} — ${Number(p.base_price).toFixed(2)} ({p.billing_interval})
                </option>
              ))}
            </select>
          </div>

          <div
            style={{
              padding: '0.85rem',
              background: 'var(--bg-subtle)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
            }}
          >
            Line items, taxes and discounts will transfer automatically into the new subscription.
          </div>
        </form>
      </Modal>

      {/* Preview Modal */}
      <Modal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        title={selectedQuote ? `Quotation ${selectedQuote.reference}` : 'Quotation Preview'}
        maxWidth="680px"
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
            <button className="btn btn-outline" onClick={() => window.print()}>
              <Printer size={15} /> Print / Export
            </button>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {!isCustomer && selectedQuote?.status === 'confirmed' && (
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setIsPreviewOpen(false);
                    handleOpenConvert(selectedQuote);
                  }}
                >
                  <Repeat size={15} /> Convert to Subscription
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setIsPreviewOpen(false)}>
                Close
              </button>
            </div>
          </div>
        }
      >
        {selectedQuote && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                borderBottom: '1px solid var(--border)',
                paddingBottom: '1rem',
              }}
            >
              <div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Customer</p>
                <h3 style={{ fontSize: '1.1rem' }}>{selectedQuote.customer_name}</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Valid until: {selectedQuote.valid_until || '30 days'}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Status</p>
                <StatusBadge status={selectedQuote.status} />
              </div>
            </div>

            <table className="data-table" style={{ border: '1px solid var(--border)' }}>
              <thead>
                <tr>
                  <th>Item Description</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th>Discount</th>
                  <th style={{ textAlign: 'right' }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {(selectedQuote.lines || []).map((line, idx) => {
                  const lineSub = Number(line.quantity || 1) * Number(line.unit_price || 0) * (1 - (Number(line.discount_percent || 0) / 100));
                  return (
                    <tr key={idx}>
                      <td style={{ fontWeight: 500 }}>{line.description}</td>
                      <td>{line.quantity}</td>
                      <td>${Number(line.unit_price).toFixed(2)}</td>
                      <td>{line.discount_percent || 0}%</td>
                      <td style={{ textAlign: 'right', fontWeight: 600 }}>${lineSub.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div style={{ width: '240px', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Subtotal:</span>
                  <span>${Number(selectedQuote.subtotal || selectedQuote.total_amount || 0).toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Tax:</span>
                  <span>${Number(selectedQuote.tax_amount || 0).toFixed(2)}</span>
                </div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    borderTop: '1px solid var(--border)',
                    paddingTop: '0.5rem',
                    fontWeight: 700,
                    fontSize: '1.05rem',
                    color: 'var(--primary)',
                  }}
                >
                  <span>Grand Total:</span>
                  <span>${Number(selectedQuote.total_amount || 0).toFixed(2)}</span>
                </div>
              </div>
            </div>

            {selectedQuote.notes && (
              <div
                style={{
                  background: 'var(--bg-subtle)',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.825rem',
                  color: 'var(--text-secondary)',
                }}
              >
                <strong>Terms:</strong> {selectedQuote.notes}
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Quotation"
        maxWidth="680px"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleCreateSubmit}>
              Save Draft
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
              <label className="form-label">Valid Until</label>
              <input
                type="date"
                className="form-input"
                value={form.valid_until}
                onChange={(e) => setForm({ ...form, valid_until: e.target.value })}
                required
              />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <label className="form-label">Quotation Line Items</label>
              <button
                type="button"
                className="btn btn-outline"
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}
                onClick={handleAddLine}
              >
                <Plus size={13} /> Add Item
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
                    placeholder="Disc %"
                    value={line.discount_percent}
                    onChange={(e) => handleLineChange(idx, 'discount_percent', e.target.value)}
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

          <div className="form-group">
            <label className="form-label">Notes & Terms</label>
            <textarea
              className="form-textarea"
              rows={2}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
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
              Total: ${totals.total.toFixed(2)} {form.currency}
            </span>
          </div>
        </form>
      </Modal>
    </div>
  );
}

