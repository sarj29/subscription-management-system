import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Building, Mail, Phone, MapPin } from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import { customerService } from '../services/customerService';
import { useAuth } from '../context/AuthContext';

export default function Customers() {
  const { isAdmin } = useAuth();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState(null);

  const [formData, setFormData] = useState({
    company_name: '',
    contact_name: '',
    email: '',
    phone: '',
    city: '',
    country: 'US',
    tax_id: '',
    notes: '',
  });

  const loadCustomers = async () => {
    setLoading(true);
    try {
      const data = await customerService.list();
      setCustomers(data);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const handleOpenCreate = () => {
    setEditingCustomer(null);
    setFormData({
      company_name: '',
      contact_name: '',
      email: '',
      phone: '',
      city: '',
      country: 'US',
      tax_id: '',
      notes: '',
    });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (customer) => {
    setEditingCustomer(customer);
    setFormData({
      company_name: customer.company_name || '',
      contact_name: customer.contact_name || '',
      email: customer.email || '',
      phone: customer.phone || '',
      city: customer.city || '',
      country: customer.country || 'US',
      tax_id: customer.tax_id || '',
      notes: customer.notes || '',
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCustomer) {
        await customerService.update(editingCustomer.id, formData);
      } else {
        await customerService.create(formData);
      }
      setIsModalOpen(false);
      loadCustomers();
    } catch (err) {
      alert(err.message || 'Error saving customer');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this customer?')) return;
    try {
      await customerService.delete(id);
      loadCustomers();
    } catch (err) {
      alert(err.message || 'Error deleting customer');
    }
  };

  const columns = [
    {
      header: 'Company & Contact',
      accessor: 'company_name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Building size={16} color="var(--primary)" />
            {row.company_name}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{row.contact_name}</div>
        </div>
      ),
    },
    {
      header: 'Email',
      accessor: 'email',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Mail size={14} color="var(--text-muted)" />
          <span>{row.email}</span>
        </div>
      ),
    },
    {
      header: 'Location',
      accessor: 'city',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <MapPin size={14} color="var(--text-muted)" />
          <span>{row.city ? `${row.city}, ${row.country}` : row.country || 'Global'}</span>
        </div>
      ),
    },
    {
      header: 'Tax ID / VAT',
      accessor: 'tax_id',
      render: (row) => <span style={{ fontFamily: 'monospace', fontSize: '0.825rem' }}>{row.tax_id || '—'}</span>,
    },
    {
      header: 'Actions',
      width: '120px',
      align: 'right',
      render: (row) => (
        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
          <button className="btn-icon" onClick={() => handleOpenEdit(row)} title="Edit Customer">
            <Edit2 size={15} />
          </button>
          {isAdmin && (
            <button
              className="btn-icon"
              onClick={() => handleDelete(row.id)}
              title="Delete Customer"
              style={{ color: 'var(--danger)' }}
            >
              <Trash2 size={15} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Customers</h1>
          <p className="page-subtitle">Manage client accounts, contact details, and billing profiles.</p>
        </div>
        <button className="btn btn-primary" onClick={handleOpenCreate}>
          <Plus size={16} /> Add Customer
        </button>
      </div>

      <DataTable
        columns={columns}
        data={customers}
        loading={loading}
        searchPlaceholder="Search company, contact, or email..."
        searchField="company_name"
      />

      {/* Create / Edit Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingCustomer ? 'Edit Customer Profile' : 'Add New Customer'}
      >
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Company Name *</label>
              <input
                className="form-input"
                value={formData.company_name}
                onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Contact Name *</label>
              <input
                className="form-input"
                value={formData.contact_name}
                onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Email Address *</label>
              <input
                type="email"
                className="form-input"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input
                className="form-input"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">City</label>
              <input
                className="form-input"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Country Code</label>
              <input
                className="form-input"
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                placeholder="US, UK, DE, etc."
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Tax ID / VAT Number</label>
            <input
              className="form-input"
              value={formData.tax_id}
              onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
              placeholder="e.g. US-12345678"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Notes & Preferences</label>
            <textarea
              className="form-textarea"
              rows={3}
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Payment terms, contract specifics, etc."
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {editingCustomer ? 'Save Changes' : 'Create Customer'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
