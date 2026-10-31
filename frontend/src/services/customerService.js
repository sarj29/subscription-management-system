import api from './api';
import { initialCustomers } from './mockData';

const STORAGE_KEY = 'brightloop_customers';

function getLocal() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : initialCustomers;
}

function saveLocal(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const customerService = {
  async list(params = {}) {
    try {
      const res = await api.get('/customers/', { params });
      return res.data;
    } catch {
      let items = getLocal();
      if (params.search) {
        const q = params.search.toLowerCase();
        items = items.filter(
          (c) =>
            c.company_name?.toLowerCase().includes(q) ||
            c.contact_name?.toLowerCase().includes(q) ||
            c.email?.toLowerCase().includes(q)
        );
      }
      if (params.city) {
        items = items.filter((c) => c.city?.toLowerCase().includes(params.city.toLowerCase()));
      }
      return items;
    }
  },

  async get(id) {
    try {
      const res = await api.get(`/customers/${id}`);
      return res.data;
    } catch {
      const items = getLocal();
      const item = items.find((c) => c.id === id);
      if (!item) throw new Error('Customer not found');
      return item;
    }
  },

  async create(data) {
    try {
      const res = await api.post('/customers/', data);
      return res.data;
    } catch {
      const items = getLocal();
      const newCust = {
        ...data,
        id: `cust-${Date.now().toString().slice(-4)}`,
        created_at: new Date().toISOString(),
      };
      items.unshift(newCust);
      saveLocal(items);
      return newCust;
    }
  },

  async update(id, data) {
    try {
      const res = await api.patch(`/customers/${id}`, data);
      return res.data;
    } catch {
      const items = getLocal();
      const idx = items.findIndex((c) => c.id === id);
      if (idx === -1) throw new Error('Customer not found');
      items[idx] = { ...items[idx], ...data };
      saveLocal(items);
      return items[idx];
    }
  },

  async delete(id) {
    try {
      await api.delete(`/customers/${id}`);
    } catch {
      const items = getLocal().filter((c) => c.id !== id);
      saveLocal(items);
    }
  },
};
