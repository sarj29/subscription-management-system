import api from './api';
import { initialQuotations } from './mockData';
import { subscriptionService } from './subscriptionService';

const STORAGE_KEY = 'brightloop_quotations';

function getLocal() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : initialQuotations;
}

function saveLocal(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const quotationService = {
  async list(params = {}) {
    try {
      const res = await api.get('/quotations/', { params });
      return res.data;
    } catch {
      let items = getLocal();
      if (params.status) {
        items = items.filter((q) => q.status === params.status);
      }
      if (params.search) {
        const query = params.search.toLowerCase();
        items = items.filter(
          (q) =>
            q.reference?.toLowerCase().includes(query) ||
            q.customer_name?.toLowerCase().includes(query) ||
            q.notes?.toLowerCase().includes(query)
        );
      }
      return items;
    }
  },

  async get(id) {
    try {
      const res = await api.get(`/quotations/${id}`);
      return res.data;
    } catch {
      const items = getLocal();
      const item = items.find((q) => q.id === id);
      if (!item) throw new Error('Quotation not found');
      return item;
    }
  },

  async create(data) {
    try {
      const res = await api.post('/quotations/', data);
      return res.data;
    } catch {
      const items = getLocal();
      const lines = data.lines || [];
      const subtotal = lines.reduce((acc, l) => acc + Number(l.quantity) * Number(l.unit_price) * (1 - (Number(l.discount_percent) || 0) / 100), 0);
      const tax_amount = lines.reduce((acc, l) => {
        const lineSub = Number(l.quantity) * Number(l.unit_price) * (1 - (Number(l.discount_percent) || 0) / 100);
        return acc + lineSub * ((Number(l.tax_percent) || 0) / 100);
      }, 0);

      const newQuote = {
        ...data,
        id: `quote-${Date.now().toString().slice(-4)}`,
        reference: `QT-202610-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
        status: 'draft',
        subtotal: Number(subtotal.toFixed(2)),
        tax_amount: Number(tax_amount.toFixed(2)),
        total_amount: Number((subtotal + tax_amount).toFixed(2)),
        created_at: new Date().toISOString(),
      };
      items.unshift(newQuote);
      saveLocal(items);
      return newQuote;
    }
  },

  async updateStatus(id, newStatus) {
    try {
      const res = await api.post(`/quotations/${id}/status`, { status: newStatus });
      return res.data;
    } catch {
      const items = getLocal();
      const quote = items.find((q) => q.id === id);
      if (!quote) throw new Error('Quotation not found');
      quote.status = newStatus;
      saveLocal(items);
      return quote;
    }
  },

  async convertToSubscription(id, planId) {
    try {
      const res = await api.post(`/quotations/${id}/convert-to-subscription`, {
        plan_id: planId,
      });
      return res.data;
    } catch {
      const items = getLocal();
      const quote = items.find((q) => q.id === id);
      if (!quote) throw new Error('Quotation not found');

      // Create subscription in mock store
      const sub = await subscriptionService.create({
        customer_id: quote.customer_id,
        customer_name: quote.customer_name,
        plan_id: planId,
        quotation_id: quote.id,
        status: 'confirmed',
        currency: quote.currency || 'USD',
        lines: quote.lines,
        notes: `Converted from quotation ${quote.reference}`,
      });

      quote.status = 'confirmed';
      saveLocal(items);
      return sub;
    }
  },
};
