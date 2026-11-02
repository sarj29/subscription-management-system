import React, { useState, useEffect } from 'react';
import {
  Plus,
  CreditCard,
  CheckCircle2,
  DollarSign,
  ArrowUpRight,
} from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import StatusBadge from '../components/StatusBadge';
import { paymentService } from '../services/paymentService';
import { invoiceService } from '../services/invoiceService';
import { customerService } from '../services/customerService';
import { useAuth } from '../context/AuthContext';

export default function Payments() {
  const { isCustomer } = useAuth();
  const [payments, setPayments] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [notice, setNotice] = useState('');

  const [form, setForm] = useState({
    customer_id: '',
    invoice_id: '',
    amount: '199.00',
    payment_method: 'credit_card',
    notes: 'Payment settled in full',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [paysData, invsData, custsData] = await Promise.all([
        paymentService.list(),
        invoiceService.list(),
        customerService.list(),
      ]);
      setPayments(paysData);
      setInvoices(invsData);
      setCustomers(custsData);

      if (custsData.length > 0 && !form.customer_id) {
        setForm((prev) => ({ ...prev, customer_id: custsData[0].id }));
      }
    } catch (err) {
      console.error('Failed to load payments:', err);
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
    const defaultCust = customers[0]?.id || '';
    const openInvs = invoices.filter(
      (i) => i.status !== 'paid' && (!defaultCust || i.customer_id === defaultCust)
    );
    const defaultInv = openInvs[0] || invoices[0];

    setForm({
      customer_id: defaultCust,
      invoice_id: defaultInv?.id || '',
      amount: String(defaultInv?.total_amount || '199.00'),
      payment_method: 'credit_card',
      notes: defaultInv ? `Settlement for invoice ${defaultInv.invoice_number}` : 'Payment recorded',
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const selCust = customers.find((c) => c.id === form.customer_id);
      const selInv = invoices.find((i) => i.id === form.invoice_id);

      await paymentService.record({
        ...form,
        customer_name: selCust?.company_name || 'Client',
        invoice_number: selInv?.invoice_number || 'INV-MANUAL',
        amount: parseFloat(form.amount) || 0,
      });

      setIsModalOpen(false);
      showNotice('Payment transaction recorded successfully.');
      loadData();
    } catch (err) {
      alert(err.message || 'Error recording payment');
    }
  };

  const totalCollected = payments.reduce((acc, p) => acc + Number(p.amount || 0), 0);

  const columns = [
    {
      header: 'Payment #',
      accessor: 'payment_number',
      render: (row) => (
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {row.payment_number}
        </span>
      ),
    },
    {
      header: 'Invoice Reference',
      accessor: 'invoice_number',
      render: (row) => (
        <span style={{ fontWeight: 500 }}>{row.invoice_number || 'Direct Payment'}</span>
      ),
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
      render: (row) => <span>{row.customer_name || 'Acme Client'}</span>,
    },
    {
      header: 'Amount',
      accessor: 'amount',
      render: (row) => (
        <span style={{ fontWeight: 600, color: 'var(--success)' }}>
          +${Number(row.amount || 0).toFixed(2)}
        </span>
      ),
    },
    {
      header: 'Method',
      accessor: 'payment_method',
      render: (row) => {
        const methodMap = {
          credit_card: 'Credit Card / Stripe',
          bank_transfer: 'Bank Transfer (ACH)',
          paypal: 'PayPal',
          cash: 'Manual Cash',
        };
        return (
          <span style={{ textTransform: 'capitalize', fontSize: '0.85rem' }}>
            {methodMap[row.payment_method] || row.payment_method}
          </span>
        );
      },
    },
    {
      header: 'Recorded At',
      accessor: 'recorded_at',
      render: (row) => (
        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          {row.recorded_at ? new Date(row.recorded_at).toLocaleDateString() : 'Today'}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (row) => <StatusBadge status={row.status || 'recorded'} />,
    },
  ];

  const filterOptions = [
    { label: 'Recorded', value: 'recorded' },
    { label: 'Reversed', value: 'reversed' },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Payments</h1>
          <p className="page-subtitle">
            Audit settled payments, payment methods and automatic invoice reconciliations.
          </p>
        </div>
        {!isCustomer && (
          <div className="header-actions">
            <button className="btn btn-primary" onClick={handleOpenCreate}>
              <Plus size={16} /> Record Payment
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

      {/* Mini-metric bar */}
      <div
        style={{
          display: 'flex',
          gap: '1.5rem',
          background: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-lg)',
          padding: '1rem 1.5rem',
          marginBottom: '1.5rem',
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 'var(--radius-md)',
              background: 'var(--success-bg)',
              color: 'var(--success)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <DollarSign size={20} />
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Total Reconciled Collections
            </span>
            <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-primary)' }}>
              ${totalCollected.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        <div style={{ height: 28, width: 1, background: 'var(--border)' }} />

        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Settled Receipts
          </span>
          <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            {payments.length} successful transactions
          </div>
        </div>
      </div>

      <DataTable
        columns={columns}
        data={payments}
        loading={loading}
        searchPlaceholder="Search payment #, invoice or customer..."
        searchField="payment_number"
        filterKey="status"
        filterOptions={filterOptions}
        emptyMessage="No payment records found"
      />

      {/* Record Payment Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Record New Payment"
        maxWidth="520px"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSubmit}>
              Record Transaction
            </button>
          </>
        }
      >
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Customer</label>
            <select
              className="form-select"
              value={form.customer_id}
              onChange={(e) => {
                const newCust = e.target.value;
                const custInvs = invoices.filter((i) => i.customer_id === newCust && i.status !== 'paid');
                setForm({
                  ...form,
                  customer_id: newCust,
                  invoice_id: custInvs[0]?.id || '',
                  amount: custInvs[0] ? String(custInvs[0].total_amount) : form.amount,
                });
              }}
              required
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.company_name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Link to Invoice</label>
            <select
              className="form-select"
              value={form.invoice_id}
              onChange={(e) => {
                const inv = invoices.find((i) => i.id === e.target.value);
                setForm({
                  ...form,
                  invoice_id: e.target.value,
                  amount: inv ? String(inv.total_amount) : form.amount,
                  notes: inv ? `Settlement for invoice ${inv.invoice_number}` : form.notes,
                });
              }}
              required
            >
              <option value="">-- Select an invoice --</option>
              {invoices.map((inv) => (
                <option key={inv.id} value={inv.id}>
                  {inv.invoice_number} — ${Number(inv.total_amount).toFixed(2)} ({inv.status})
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Payment Amount ($)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                className="form-input"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Payment Method</label>
              <select
                className="form-select"
                value={form.payment_method}
                onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
              >
                <option value="credit_card">Credit Card (Stripe)</option>
                <option value="bank_transfer">Bank Transfer (ACH)</option>
                <option value="paypal">PayPal</option>
                <option value="cash">Manual Cash / Check</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Transaction Reference & Notes</label>
            <input
              type="text"
              className="form-input"
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </div>
        </form>
      </Modal>
    </div>
  );
}

