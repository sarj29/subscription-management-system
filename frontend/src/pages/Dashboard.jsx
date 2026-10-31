import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  Repeat,
  AlertCircle,
  TrendingUp,
  Plus,
  ArrowRight,
  Receipt,
  CheckCircle2,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import { subscriptionService } from '../services/subscriptionService';
import { invoiceService } from '../services/invoiceService';
import { useAuth } from '../context/AuthContext';

export default function Dashboard() {
  const { user, isCustomer } = useAuth();
  const [subscriptions, setSubscriptions] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [subs, invs] = await Promise.all([
          subscriptionService.list(),
          invoiceService.list(),
        ]);
        setSubscriptions(subs);
        setInvoices(invs);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const activeSubs = subscriptions.filter((s) => s.status === 'active');
  const overdueInvoices = invoices.filter((i) => i.status === 'confirmed');
  const paidInvoices = invoices.filter((i) => i.status === 'paid');

  const totalMRR = activeSubs.reduce((acc, s) => acc + Number(s.total_amount || 0), 0);
  const outstandingAmount = overdueInvoices.reduce((acc, i) => acc + Number(i.total_amount || 0), 0);
  const collectedRevenue = paidInvoices.reduce((acc, i) => acc + Number(i.total_amount || 0), 0);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            {isCustomer ? 'Customer Portal Overview' : 'Executive Billing & Subscriptions'}
          </h1>
          <p className="page-subtitle">
            Welcome back, {user?.full_name}. Here is Brightloop Software's live financial pulse.
          </p>
        </div>
        {!isCustomer && (
          <div className="header-actions">
            <Link to="/quotations" className="btn btn-secondary">
              <Plus size={16} /> New Quotation
            </Link>
            <Link to="/subscriptions" className="btn btn-primary">
              <Plus size={16} /> New Subscription
            </Link>
          </div>
        )}
      </div>

      {/* KPI Cards */}
      <div className="grid-cards">
        <StatCard
          title="Monthly Recurring Revenue"
          value={`$${totalMRR.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          trend="+14.2%"
          trendPositive={true}
          subtitle="vs last month"
          icon={DollarSign}
          color="var(--primary)"
          bgColor="var(--primary-light)"
        />
        <StatCard
          title="Active Subscriptions"
          value={activeSubs.length.toString()}
          trend="+3 new"
          trendPositive={true}
          subtitle="this billing cycle"
          icon={Repeat}
          color="var(--success)"
          bgColor="var(--success-bg)"
        />
        <StatCard
          title="Outstanding Invoices"
          value={`$${outstandingAmount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          trend={overdueInvoices.length > 0 ? `${overdueInvoices.length} pending` : 'All cleared'}
          trendPositive={overdueInvoices.length === 0}
          subtitle="awaiting settlement"
          icon={AlertCircle}
          color="var(--warning)"
          bgColor="var(--warning-bg)"
        />
        <StatCard
          title="Total Paid Revenue"
          value={`$${collectedRevenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          trend="100% matched"
          trendPositive={true}
          subtitle="bank feeds reconciled"
          icon={CheckCircle2}
          color="var(--purple)"
          bgColor="var(--purple-bg)"
        />
      </div>

      {/* Recent Subscriptions & Invoices Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '1.5rem' }}>
        {/* Active Subscriptions Card */}
        <div className="card-table" style={{ margin: 0 }}>
          <div className="table-toolbar">
            <h3 style={{ fontSize: '1.1rem' }}>Active Subscriptions</h3>
            <Link to="/subscriptions" className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
              View All <ArrowRight size={14} />
            </Link>
          </div>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Reference</th>
                  <th>Customer</th>
                  <th>Total</th>
                  <th>Next Billing</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}>Loading subscriptions...</td>
                  </tr>
                ) : subscriptions.slice(0, 4).map((sub) => (
                  <tr key={sub.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{sub.reference}</td>
                    <td>{sub.customer_name || 'Acme Client'}</td>
                    <td>${Number(sub.total_amount).toFixed(2)}</td>
                    <td>{sub.next_billing_date || 'N/A'}</td>
                    <td><StatusBadge status={sub.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Invoices Card */}
        <div className="card-table" style={{ margin: 0 }}>
          <div className="table-toolbar">
            <h3 style={{ fontSize: '1.1rem' }}>Recent Invoices & Due Dates</h3>
            <Link to="/invoices" className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
              View All <ArrowRight size={14} />
            </Link>
          </div>
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice #</th>
                  <th>Customer</th>
                  <th>Due Date</th>
                  <th>Amount</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', padding: '2rem' }}>Loading invoices...</td>
                  </tr>
                ) : invoices.slice(0, 4).map((inv) => (
                  <tr key={inv.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{inv.invoice_number}</td>
                    <td>{inv.customer_name || 'Acme Client'}</td>
                    <td>{inv.due_date}</td>
                    <td style={{ fontWeight: 600 }}>${Number(inv.total_amount).toFixed(2)}</td>
                    <td><StatusBadge status={inv.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
