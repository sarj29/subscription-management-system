import api from './api';
import { initialInvoices } from './mockData';

const STORAGE_KEY = 'brightloop_invoices';

function getLocal() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : initialInvoices;
}

function saveLocal(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const invoiceService = {
  async list(params = {}) {
    try {
      const res = await api.get('/invoices/', { params });
      return res.data;
    } catch {
      let items = getLocal();
      if (params.status) {
        items = items.filter((inv) => inv.status === params.status);
      }
      if (params.search) {
        const query = params.search.toLowerCase();
        items = items.filter(
          (inv) =>
            inv.invoice_number?.toLowerCase().includes(query) ||
            inv.customer_name?.toLowerCase().includes(query) ||
            inv.notes?.toLowerCase().includes(query)
        );
      }
      return items;
    }
  },

  async get(id) {
    try {
      const res = await api.get(`/invoices/${id}`);
      return res.data;
    } catch {
      const items = getLocal();
      const item = items.find((inv) => inv.id === id);
      if (!item) throw new Error('Invoice not found');
      return item;
    }
  },

  async create(data) {
    try {
      const res = await api.post('/invoices/', data);
      return res.data;
    } catch {
      const items = getLocal();
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + 14);

      const newInv = {
        ...data,
        id: `inv-${Date.now().toString().slice(-4)}`,
        invoice_number: `INV-202610-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
        status: data.status || 'draft',
        issue_date: new Date().toISOString().split('T')[0],
        due_date: dueDate.toISOString().split('T')[0],
      };
      items.unshift(newInv);
      saveLocal(items);
      return newInv;
    }
  },

  async updateStatus(id, newStatus) {
    try {
      const res = await api.post(`/invoices/${id}/status`, { status: newStatus });
      return res.data;
    } catch {
      const items = getLocal();
      const inv = items.find((i) => i.id === id);
      if (!inv) throw new Error('Invoice not found');
      inv.status = newStatus;
      if (newStatus === 'paid') {
        inv.paid_at = new Date().toISOString();
      }
      saveLocal(items);
      return inv;
    }
  },
};
