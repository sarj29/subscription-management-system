import api from './api';
import { initialSubscriptions } from './mockData';
import { invoiceService } from './invoiceService';

const STORAGE_KEY = 'brightloop_subscriptions';

function getLocal() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : initialSubscriptions;
}

function saveLocal(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const subscriptionService = {
  async list(params = {}) {
    try {
      const res = await api.get('/subscriptions/', { params });
      return res.data;
    } catch {
      let items = getLocal();
      if (params.status) {
        items = items.filter((s) => s.status === params.status);
      }
      if (params.search) {
        const query = params.search.toLowerCase();
        items = items.filter(
          (s) =>
            s.reference?.toLowerCase().includes(query) ||
            s.customer_name?.toLowerCase().includes(query) ||
            s.plan_name?.toLowerCase().includes(query)
        );
      }
      return items;
    }
  },

  async get(id) {
    try {
      const res = await api.get(`/subscriptions/${id}`);
      return res.data;
    } catch {
      const items = getLocal();
      const item = items.find((s) => s.id === id);
      if (!item) throw new Error('Subscription not found');
      return item;
    }
  },

  async create(data) {
    try {
      const res = await api.post('/subscriptions/', data);
      return res.data;
    } catch {
      const items = getLocal();
      const lines = data.lines || [];
      const subtotal = lines.reduce((acc, l) => acc + Number(l.quantity) * Number(l.unit_price) * (1 - (Number(l.discount_percent) || 0) / 100), 0);
      const tax_amount = lines.reduce((acc, l) => {
        const lineSub = Number(l.quantity) * Number(l.unit_price) * (1 - (Number(l.discount_percent) || 0) / 100);
        return acc + lineSub * ((Number(l.tax_percent) || 0) / 100);
      }, 0);

      const nextDate = new Date();
      nextDate.setMonth(nextDate.getMonth() + 1);

      const newSub = {
        ...data,
        id: `sub-${Date.now().toString().slice(-4)}`,
        reference: `SUB-202610-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
        status: data.status || 'draft',
        start_date: data.start_date || new Date().toISOString().split('T')[0],
        next_billing_date: nextDate.toISOString().split('T')[0],
        subtotal: Number(subtotal.toFixed(2)),
        tax_amount: Number(tax_amount.toFixed(2)),
        total_amount: Number((subtotal + tax_amount).toFixed(2)),
      };
      items.unshift(newSub);
      saveLocal(items);
      return newSub;
    }
  },

  async pause(id) {
    try {
      const res = await api.post(`/subscriptions/${id}/pause`);
      return res.data;
    } catch {
      const items = getLocal();
      const sub = items.find((s) => s.id === id);
      if (!sub) throw new Error('Subscription not found');
      sub.status = 'paused';
      saveLocal(items);
      return sub;
    }
  },

  async resume(id) {
    try {
      const res = await api.post(`/subscriptions/${id}/resume`);
      return res.data;
    } catch {
      const items = getLocal();
      const sub = items.find((s) => s.id === id);
      if (!sub) throw new Error('Subscription not found');
      sub.status = 'active';
      saveLocal(items);
      return sub;
    }
  },

  async close(id, reason = 'Customer request') {
    try {
      const res = await api.post(`/subscriptions/${id}/close`, { reason });
      return res.data;
    } catch {
      const items = getLocal();
      const sub = items.find((s) => s.id === id);
      if (!sub) throw new Error('Subscription not found');
      sub.status = 'closed';
      sub.end_date = new Date().toISOString().split('T')[0];
      saveLocal(items);
      return sub;
    }
  },

  async renew(id) {
    try {
      const res = await api.post(`/subscriptions/${id}/renew`);
      return res.data;
    } catch {
      const items = getLocal();
      const sub = items.find((s) => s.id === id);
      if (!sub) throw new Error('Subscription not found');
      sub.status = 'active';
      const nextDate = new Date();
      nextDate.setMonth(nextDate.getMonth() + 1);
      sub.next_billing_date = nextDate.toISOString().split('T')[0];
      saveLocal(items);
      return sub;
    }
  },

  async generateInvoice(id, dueDays = 14) {
    try {
      const res = await api.post(`/subscriptions/${id}/invoices?due_days=${dueDays}`);
      return res.data;
    } catch {
      const sub = await this.get(id);
      const inv = await invoiceService.create({
        customer_id: sub.customer_id,
        customer_name: sub.customer_name,
        subscription_id: sub.id,
        subscription_ref: sub.reference,
        status: 'draft',
        currency: sub.currency,
        subtotal: sub.subtotal,
        tax_amount: sub.tax_amount,
        total_amount: sub.total_amount,
        notes: `Generated from subscription ${sub.reference}`,
        lines: sub.lines,
      });
      return inv;
    }
  },
};
