import React, { useState, useEffect } from 'react';
import {
  Plus,
  Layers,
  Edit2,
  Trash2,
  CheckCircle2,
  Clock,
  Check,
  X,
} from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import { planService } from '../services/planService';
import { useAuth } from '../context/AuthContext';

export default function Plans() {
  const { isAdmin } = useAuth();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [notice, setNotice] = useState('');

  const [form, setForm] = useState({
    name: '',
    description: '',
    billing_interval: 'monthly',
    interval_count: 1,
    base_price: '49.00',
    currency: 'USD',
    trial_days: 14,
    min_quantity: 1,
    allow_pause: true,
    allow_early_closure: true,
    allow_renewal: true,
    is_active: true,
  });

  const loadPlans = async () => {
    setLoading(true);
    try {
      const data = await planService.list();
      setPlans(data);
    } catch (err) {
      console.error('Failed to load plans:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlans();
  }, []);

  const showNotice = (msg) => {
    setNotice(msg);
    setTimeout(() => setNotice(''), 4000);
  };

  const handleOpenCreate = () => {
    setEditingPlan(null);
    setForm({
      name: '',
      description: '',
      billing_interval: 'monthly',
      interval_count: 1,
      base_price: '49.00',
      currency: 'USD',
      trial_days: 14,
      min_quantity: 1,
      allow_pause: true,
      allow_early_closure: true,
      allow_renewal: true,
      is_active: true,
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (plan) => {
    setEditingPlan(plan);
    setForm({
      name: plan.name || '',
      description: plan.description || '',
      billing_interval: plan.billing_interval || 'monthly',
      interval_count: plan.interval_count || 1,
      base_price: String(plan.base_price || '0.00'),
      currency: plan.currency || 'USD',
      trial_days: plan.trial_days ?? 14,
      min_quantity: plan.min_quantity ?? 1,
      allow_pause: plan.allow_pause ?? true,
      allow_early_closure: plan.allow_early_closure ?? true,
      allow_renewal: plan.allow_renewal ?? true,
      is_active: plan.is_active ?? true,
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...form,
        base_price: parseFloat(form.base_price) || 0,
        trial_days: parseInt(form.trial_days, 10) || 0,
        min_quantity: parseInt(form.min_quantity, 10) || 1,
        interval_count: parseInt(form.interval_count, 10) || 1,
      };

      if (editingPlan) {
        await planService.update(editingPlan.id, payload);
        showNotice('Plan updated successfully.');
      } else {
        await planService.create(payload);
        showNotice('New plan tier created.');
      }

      setIsModalOpen(false);
      loadPlans();
    } catch (err) {
      alert(err.message || 'Error saving plan');
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete the plan "${name}"?`)) return;
    try {
      await planService.delete(id);
      showNotice(`Plan "${name}" removed.`);
      loadPlans();
    } catch (err) {
      alert(err.message || 'Error deleting plan');
    }
  };

  const handleToggleActive = async (plan) => {
    try {
      await planService.update(plan.id, { is_active: !plan.is_active });
      loadPlans();
    } catch (err) {
      alert(err.message || 'Error updating status');
    }
  };

  const columns = [
    {
      header: 'Plan Details',
      accessor: 'name',
      render: (row) => (
        <div>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{row.name}</span>
          {row.description && (
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', maxWidth: 320, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {row.description}
            </div>
          )}
        </div>
      ),
    },
    {
      header: 'Interval',
      accessor: 'billing_interval',
      render: (row) => (
        <span
          style={{
            textTransform: 'capitalize',
            background: 'var(--bg-subtle)',
            padding: '0.2rem 0.55rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.8rem',
            fontWeight: 500,
          }}
        >
          {row.interval_count > 1 ? `Every ${row.interval_count} ` : ''}
          {row.billing_interval}
        </span>
      ),
    },
    {
      header: 'Base Price',
      accessor: 'base_price',
      render: (row) => (
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          ${Number(row.base_price || 0).toFixed(2)}
        </span>
      ),
    },
    {
      header: 'Free Trial',
      accessor: 'trial_days',
      render: (row) => (
        <span style={{ fontSize: '0.85rem' }}>
          {row.trial_days > 0 ? `${row.trial_days} days` : 'None'}
        </span>
      ),
    },
    {
      header: 'Status',
      accessor: 'is_active',
      render: (row) => (
        <span
          className={`badge ${row.is_active ? 'badge-active' : 'badge-closed'}`}
          style={{ cursor: isAdmin ? 'pointer' : 'default' }}
          onClick={() => isAdmin && handleToggleActive(row)}
          title={isAdmin ? 'Click to toggle status' : undefined}
        >
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      header: 'Actions',
      align: 'right',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.4rem' }}>
          {isAdmin && (
            <>
              <button
                className="btn-icon"
                onClick={() => handleOpenEdit(row)}
                title="Edit Plan"
              >
                <Edit2 size={15} />
              </button>
              <button
                className="btn-icon"
                onClick={() => handleDelete(row.id, row.name)}
                title="Delete Plan"
                style={{ color: 'var(--danger)' }}
              >
                <Trash2 size={15} />
              </button>
            </>
          )}
        </div>
      ),
    },
  ];

  const filterOptions = [
    { label: 'Monthly', value: 'monthly' },
    { label: 'Yearly', value: 'yearly' },
    { label: 'Quarterly', value: 'quarterly' },
    { label: 'Weekly', value: 'weekly' },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Subscription Plans</h1>
          <p className="page-subtitle">
            Configure pricing tiers, billing cadences and customer subscription rules.
          </p>
        </div>
        {isAdmin && (
          <div className="header-actions">
            <button className="btn btn-primary" onClick={handleOpenCreate}>
              <Plus size={16} /> New Plan
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
        data={plans}
        loading={loading}
        searchPlaceholder="Search plans by name or interval..."
        searchField="name"
        filterKey="billing_interval"
        filterOptions={filterOptions}
        emptyMessage="No subscription plans configured"
      />

      {/* Plan Form Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingPlan ? 'Edit Subscription Plan' : 'Create Subscription Plan'}
        maxWidth="560px"
        footer={
          <>
            <button className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSubmit}>
              {editingPlan ? 'Update Plan' : 'Create Plan'}
            </button>
          </>
        }
      >
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Plan Name</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Pro Monthly, Enterprise Cloud"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              rows={2}
              placeholder="Features or benefits of this pricing tier"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Billing Interval</label>
              <select
                className="form-select"
                value={form.billing_interval}
                onChange={(e) => setForm({ ...form, billing_interval: e.target.value })}
              >
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
                <option value="quarterly">Quarterly</option>
                <option value="weekly">Weekly</option>
                <option value="daily">Daily</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Interval Count</label>
              <input
                type="number"
                min="1"
                className="form-input"
                value={form.interval_count}
                onChange={(e) => setForm({ ...form, interval_count: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Base Price ($ USD)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="form-input"
                value={form.base_price}
                onChange={(e) => setForm({ ...form, base_price: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Trial Period (Days)</label>
              <input
                type="number"
                min="0"
                className="form-input"
                value={form.trial_days}
                onChange={(e) => setForm({ ...form, trial_days: e.target.value })}
              />
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.65rem',
              padding: '0.85rem',
              background: 'var(--bg-subtle)',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.85rem',
            }}
          >
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.allow_pause}
                onChange={(e) => setForm({ ...form, allow_pause: e.target.checked })}
              />
              Allow Customer to Pause Subscription
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.allow_renewal}
                onChange={(e) => setForm({ ...form, allow_renewal: e.target.checked })}
              />
              Enable Automatic Cycle Renewal
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
              />
              Plan is Active & Available for Subscriptions
            </label>
          </div>
        </form>
      </Modal>
    </div>
  );
}

