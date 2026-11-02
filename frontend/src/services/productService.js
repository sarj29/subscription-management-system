import api from './api';
import { initialProducts } from './mockData';

const STORAGE_KEY = 'brightloop_products';

function getLocal() {
  const data = localStorage.getItem(STORAGE_KEY);
  return data ? JSON.parse(data) : initialProducts;
}

function saveLocal(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const productService = {
  async list(params = {}) {
    try {
      const res = await api.get('/products/', { params });
      return res.data;
    } catch {
      let items = getLocal();
      if (params.search) {
        const q = params.search.toLowerCase();
        items = items.filter(
          (p) =>
            p.name?.toLowerCase().includes(q) ||
            p.sku?.toLowerCase().includes(q) ||
            p.description?.toLowerCase().includes(q)
        );
      }
      return items;
    }
  },

  async get(id) {
    try {
      const res = await api.get(`/products/${id}`);
      return res.data;
    } catch {
      const items = getLocal();
      const item = items.find((p) => p.id === id);
      if (!item) throw new Error('Product not found');
      return item;
    }
  },

  async create(data) {
    try {
      const res = await api.post('/products/', data);
      return res.data;
    } catch {
      const items = getLocal();
      const newProd = {
        ...data,
        id: `prod-${Date.now().toString().slice(-4)}`,
        variants: (data.variants || []).map((v, i) => ({
          ...v,
          id: `var-${Date.now().toString().slice(-4)}-${i}`,
          product_id: `prod-${Date.now().toString().slice(-4)}`,
        })),
      };
      items.unshift(newProd);
      saveLocal(items);
      return newProd;
    }
  },

  async addVariant(productId, variantData) {
    try {
      const res = await api.post(`/products/${productId}/variants`, variantData);
      return res.data;
    } catch {
      const items = getLocal();
      const prod = items.find((p) => p.id === productId);
      if (!prod) throw new Error('Product not found');
      const newVar = {
        ...variantData,
        id: `var-${Date.now().toString().slice(-4)}`,
        product_id: productId,
      };
      prod.variants.push(newVar);
      saveLocal(items);
      return newVar;
    }
  },

  async adjustVariantPrice(productId, variantId, adjustment) {
    try {
      const res = await api.post(`/products/${productId}/variants/${variantId}/adjust-price`, {
        adjustment,
      });
      return res.data;
    } catch {
      const items = getLocal();
      const prod = items.find((p) => p.id === productId);
      if (!prod) throw new Error('Product not found');
      const variant = prod.variants.find((v) => v.id === variantId);
      if (!variant) throw new Error('Variant not found');
      variant.unit_price = Number(variant.unit_price) + Number(adjustment);
      saveLocal(items);
      return variant;
    }
  },

  async delete(id) {
    try {
      await api.delete(`/products/${id}`);
    } catch {
      const items = getLocal().filter((p) => p.id !== id);
      saveLocal(items);
    }
  },
};
