import React, { useState, useEffect } from 'react';
import {
  Plus,
  Receipt,
  Eye,
  CheckCircle,
  CreditCard,
  Printer,
  XCircle,
  CheckCircle2,
} from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { invoiceService } from '../services/invoiceService';
import { paymentService } from '../services/paymentService';
import { customerService } from '../services/customerService';
import { useAuth } from '../context/AuthContext';

export default function Invoices() {
  const { isCustomer } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isPayOpen, setIsPayOpen] = useState(false);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [notice, setNotice] = useState('');

  // Payment form state
  const [payForm, setPayForm] = useState({
    amount: '',
    payment_method: 'credit_card',
    notes: 'Paid in full',
  });

  // Invoice create form
  const defaultDueDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 14);
    return d.toISOString().split('T')[0];
  };

  const [form, setForm] = useState({
    customer_id: '',
    due_date: defaultDueDate(),
    currency: 'USD',
    notes: 'Payment due within 14 days.',
    lines: [
      {
        description: 'Monthly SaaS Platform Fee',
        quantity: 1,
        unit_price: 199,
        tax_percent: 10,
      },
    ],
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [invsData, custsData] = await Promise.all([
        invoiceService.list(),
        customerService.list(),
      ]);
      setInvoices(invsData);
      setCustomers(custsData);

      if (custsData.length > 0 && !form.customer_id) {
        setForm((prev) => ({ ...prev, customer_id: custsData[0].id }));
      }
    } catch (err) {
      console.error('Failed to load invoices:', err);
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
      due_date: defaultDueDate(),
      currency: 'USD',
      notes: 'Payment due within 14 days.',
      lines: [
        {
          description: 'Standard Software Service Fee',
          quantity: 1,
          unit_price: 199,
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
          description: 'Additional Service Item',
          quantity: 1,
          unit_price: 49,
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
    const subtotal = form.lines.reduce(
      (acc, l) => acc + Number(l.quantity || 0) * Number(l.unit_price || 0),
      0
    );
    const taxAmount = form.lines.reduce((acc, l) => {
      const lineSub = Number(l.quantity || 0) * Number(l.unit_price || 0);
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
      const totals = calculateTotals();
      await invoiceService.create({
        ...form,
        customer_name: selCust?.company_name || 'Client',
        subtotal: totals.subtotal,
        tax_amount: totals.taxAmount,
        total_amount: totals.total,
        status: 'draft',
      });
      setIsCreateOpen(false);
      showNotice('Invoice created successfully as draft.');
      loadData();
    } catch (err) {
      alert(err.message || 'Error creating invoice');
    }
  };

  const handleStatusChange = async (inv, newStatus) => {
    try {
      await invoiceService.updateStatus(inv.id, newStatus);
      showNotice(`Invoice status updated to ${newStatus}.`);
      loadData();
      if (selectedInvoice?.id === inv.id) {
        setSelectedInvoice((prev) => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      alert(err.message || 'Error updating invoice status');
    }
  };

  const handleOpenPay = (inv) => {
    setSelectedInvoice(inv);
    setPayForm({
      amount: String(inv.total_amount || '0.00'),
      payment_method: 'credit_card',
      notes: `Settlement for invoice ${inv.invoice_number}`,
    });
    setIsPayOpen(true);
  };

  const handlePaySubmit = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    try {
      await paymentService.record({
        invoice_id: selectedInvoice.id,
        invoice_number: selectedInvoice.invoice_number,
        customer_id: selectedInvoice.customer_id,
        customer_name: selectedInvoice.customer_name,
        amount: parseFloat(payForm.amount) || selectedInvoice.total_amount,
        payment_method: payForm.payment_method,
        notes: payForm.notes,
      });

      setIsPayOpen(false);
      showNotice(`Payment recorded. Invoice ${selectedInvoice.invoice_number} marked as paid.`);
      loadData();
    } catch (err) {
      alert(err.message || 'Error recording payment');
    }
  };

  const columns = [
    {
      header: 'Invoice #',
      accessor: 'invoice_number',
      render: (row) => (
        <div>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.invoice_number}</span>
          {row.subscription_ref && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Via {row.subscription_ref}
            </div>
          )}
        </div>
      ),
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
      render: (row) => <span style={{ fontWeight: 500 }}>{row.customer_name || 'Acme Client'}</span>,
    },
    {
      header: 'Due Date',
      accessor: 'due_date',
      render: (row) => <span style={{ fontSize: '0.875rem' }}>{row.due_date || 'N/A'}</span>,
    },
    {
      header: 'Amount',
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
              setSelectedInvoice(row);
              setIsPreviewOpen(true);
            }}
            title="View Invoice"
          >
            <Eye size={16} />
          </button>
          {!isCustomer && (
            <>
              {row.status === 'draft' && (
                <button
                  className="btn-icon"
                  onClick={() => handleStatusChange(row, 'confirmed')}
                  title="Confirm & Issue"
                  style={{ color: 'var(--primary)' }}
                >
                  <CheckCircle size={15} />
                </button>
              )}
              {row.status === 'confirmed' && (
                <button
                  className="btn btn-outline"
                  style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem', color: 'var(--success)' }}
                  onClick={() => handleOpenPay(row)}
                  title="Record Payment"
                >
                  <CreditCard size={13} /> Pay
                </button>
              )}
              {row.status !== 'paid' && row.status !== 'cancelled' && (
                <button
                  className="btn-icon"
                  onClick={() => handleStatusChange(row, 'cancelled')}
                  title="Cancel Invoice"
                  style={{ color: 'var(--danger)' }}
                >
                  <XCircle size={15} />
                </button>
              )}
            </>
          )}
          {isCustomer && row.status === 'confirmed' && (
            <button
              className="btn btn-primary"
              style={{ fontSize: '0.75rem', padding: '0.25rem 0.6rem' }}
              onClick={() => handleOpenPay(row)}
            >
              <CreditCard size={13} /> Pay Now
            </button>
          )}
        </div>
      ),
    },
  ];

  const filterOptions = [
    { label: 'Confirmed (Awaiting Payment)', value: 'confirmed' },
    { label: 'Paid', value: 'paid' },
    { label: 'Draft', value: 'draft' },
    { label: 'Cancelled', value: 'cancelled' },
  ];

  const totals = calculateTotals();

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Invoices</h1>
          <p className="page-subtitle">
            Track generated billings, payment settlements, and transaction histories.
          </p>
        </div>
        {!isCustomer && (
          <div className="header-actions">
            <button className="btn btn-primary" onClick={handleOpenCreate}>
              <Plus size={16} /> New Invoice
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
        data={invoices}
        loading={loading}
        searchPlaceholder="Search invoice # or customer..."
        searchField="invoice_number"
        filterKey="status"
        filterOptions={filterOptions}
        emptyMessage="No invoices found"
      />

      {/* Record Payment Modal */}
      <Modal
        isOpen={isPayOpen}
        onClose={() => setIsPayOpen(false)}
        title="Record Payment"
        maxWidth="500px"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsPayOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-success" onClick={handlePaySubmit}>
              Confirm Payment
            </button>
          </>
        }
      >
        <form onSubmit={handlePaySubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Recording payment for invoice <strong>{selectedInvoice?.invoice_number}</strong> (
            {selectedInvoice?.customer_name}).
          </p>

          <div className="form-group">
            <label className="form-label">Payment Amount ($)</label>
            <input
              type="number"
              step="0.01"
              className="form-input"
              value={payForm.amount}
              onChange={(e) => setPayForm({ ...payForm, amount: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Payment Method</label>
            <select
              className="form-select"
              value={payForm.payment_method}
              onChange={(e) => setPayForm({ ...payForm, payment_method: e.target.value })}
            >
              <option value="credit_card">Credit Card / Stripe</option>
              <option value="bank_transfer">ACH / Bank Transfer</option>
              <option value="paypal">PayPal</option>
              <option value="cash">Manual / Cash</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Notes & Transaction Ref</label>
            <input
              type="text"
              className="form-input"
              value={payForm.notes}
              onChange={(e) => setPayForm({ ...payForm, notes: e.target.value })}
            />
          </div>
        </form>
      </Modal>

      {/* Invoice Preview Modal */}
      <Modal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        title={selectedInvoice ? `Invoice ${selectedInvoice.invoice_number}` : 'Invoice'}
        maxWidth="680px"
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
            <button className="btn btn-outline" onClick={() => window.print()}>
              <Printer size={15} /> Print / Download
            </button>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {selectedInvoice?.status === 'confirmed' && (
                <button
                  className="btn btn-primary"
                  onClick={() => {
                    setIsPreviewOpen(false);
                    handleOpenPay(selectedInvoice);
                  }}
                >
                  <CreditCard size={15} /> Record Payment
                </button>
              )}
              <button className="btn btn-secondary" onClick={() => setIsPreviewOpen(false)}>
                Close
              </button>
            </div>
          </div>
        }
      >
        {selectedInvoice && (
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
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Billed To</p>
                <h3 style={{ fontSize: '1.1rem' }}>{selectedInvoice.customer_name}</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Issue Date: {selectedInvoice.issue_date || 'Today'}
                </p>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Due Date: {selectedInvoice.due_date || 'In 14 days'}
                </p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Payment Status</p>
                <StatusBadge status={selectedInvoice.status} />
                {selectedInvoice.subscription_ref && (
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                    Subscription: {selectedInvoice.subscription_ref}
                  </p>
                )}
              </div>
            </div>

            <table className="data-table" style={{ border: '1px solid var(--border)' }}>
              <thead>
                <tr>
                  <th>Item Description</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th style={{ textAlign: 'right' }}>Total</th>
                </tr>
              </thead>
              <tbody>
                {(selectedInvoice.lines || [
                  {
                    description: 'Brightloop Recurring Subscription Plan',
                    quantity: 1,
                    unit_price: selectedInvoice.subtotal || selectedInvoice.total_amount,
                  },
                ]).map((line, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 500 }}>{line.description}</td>
                    <td>{line.quantity || 1}</td>
                    <td>${Number(line.unit_price || 0).toFixed(2)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>
                      ${(Number(line.quantity || 1) * Number(line.unit_price || 0)).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <div style={{ width: '240px', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Subtotal:</span>
                  <span>${Number(selectedInvoice.subtotal || selectedInvoice.total_amount || 0).toFixed(2)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Tax Amount:</span>
                  <span>${Number(selectedInvoice.tax_amount || 0).toFixed(2)}</span>
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
                  <span>Amount Due:</span>
                  <span>${Number(selectedInvoice.total_amount || 0).toFixed(2)} {selectedInvoice.currency || 'USD'}</span>
                </div>
              </div>
            </div>

            {selectedInvoice.notes && (
              <div
                style={{
                  background: 'var(--bg-subtle)',
                  padding: '0.75rem 1rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.825rem',
                  color: 'var(--text-secondary)',
                }}
              >
                <strong>Payment Instructions:</strong> {selectedInvoice.notes}
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Invoice"
        maxWidth="680px"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleCreateSubmit}>
              Save Invoice
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
              <label className="form-label">Payment Due Date</label>
              <input
                type="date"
                className="form-input"
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                required
              />
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <label className="form-label">Invoice Items</label>
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

          <div className="form-group">
            <label className="form-label">Payment Terms & Notes</label>
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

