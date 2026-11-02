import api from './api';
import { initialPlans } from './mockData';

const STORAGE_KEY = 'brightloop_plans';

function getLocal() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : initialPlans;
}

function saveLocal(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const planService = {
  async list(params = {}) {
    try {
      const res = await api.get('/plans/', { params });
      return res.data;
    } catch {
      let items = getLocal();
      if (params.billing_interval) {
        items = items.filter((p) => p.billing_interval === params.billing_interval);
      }
      if (params.search) {
        const q = params.search.toLowerCase();
        items = items.filter(
          (p) => p.name?.toLowerCase().includes(q) || p.description?.toLowerCase().includes(q)
        );
      }
      return items;
    }
  },

  async get(id) {
    try {
      const res = await api.get(`/plans/${id}`);
      return res.data;
    } catch {
      const items = getLocal();
      const item = items.find((p) => p.id === id);
      if (!item) throw new Error('Plan not found');
      return item;
    }
  },

  async create(data) {
    try {
      const res = await api.post('/plans/', data);
      return res.data;
    } catch {
      const items = getLocal();
      const newPlan = {
        ...data,
        id: `plan-${Date.now().toString().slice(-4)}`,
        created_at: new Date().toISOString(),
      };
      items.unshift(newPlan);
      saveLocal(items);
      return newPlan;
    }
  },

  async update(id, data) {
    try {
      const res = await api.patch(`/plans/${id}`, data);
      return res.data;
    } catch {
      const items = getLocal();
      const idx = items.findIndex((p) => p.id === id);
      if (idx === -1) throw new Error('Plan not found');
      items[idx] = { ...items[idx], ...data };
      saveLocal(items);
      return items[idx];
    }
  },

  async delete(id) {
    try {
      await api.delete(`/plans/${id}`);
    } catch {
      const items = getLocal().filter((p) => p.id !== id);
      saveLocal(items);
    }
  },
};
