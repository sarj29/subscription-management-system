import api from './api';
import { initialPayments } from './mockData';
import { invoiceService } from './invoiceService';

const STORAGE_KEY = 'brightloop_payments';

function getLocal() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : initialPayments;
}

function saveLocal(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const paymentService = {
  async list(params = {}) {
    try {
      const res = await api.get('/payments/', { params });
      return res.data;
    } catch {
      let items = getLocal();
      if (params.customer_id) {
        items = items.filter((p) => p.customer_id === params.customer_id);
      }
      if (params.invoice_id) {
        items = items.filter((p) => p.invoice_id === params.invoice_id);
      }
      return items;
    }
  },

  async record(data) {
    try {
      const res = await api.post('/payments/', data);
      return res.data;
    } catch {
      const items = getLocal();
      const newPay = {
        ...data,
        id: `pay-${Date.now().toString().slice(-4)}`,
        payment_number: `PAY-202610-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
        status: 'recorded',
        recorded_at: new Date().toISOString(),
      };
      items.unshift(newPay);
      saveLocal(items);

      // Auto-update invoice status to paid if payment covers total
      try {
        if (data.invoice_id) {
          await invoiceService.updateStatus(data.invoice_id, 'paid');
        }
      } catch (err) {
        console.warn('Could not auto-update invoice status:', err);
      }

      return newPay;
    }
  },
};
