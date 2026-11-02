import React, { useState, useEffect } from 'react';
import { Plus, Package, Tag, SlidersHorizontal, Trash2, CheckCircle2 } from 'lucide-react';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import { productService } from '../services/productService';
import { useAuth } from '../context/AuthContext';

export default function Products() {
  const { isAdmin } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [isVariantModalOpen, setIsVariantModalOpen] = useState(false);
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedVariant, setSelectedVariant] = useState(null);

  // Forms
  const [productForm, setProductForm] = useState({
    name: '',
    sku: '',
    description: '',
    base_price: '199.00',
    variant_name: 'Standard Edition',
  });

  const [variantForm, setVariantForm] = useState({
    name: '',
    sku: '',
    unit_price: '100.00',
    currency: 'USD',
  });

  const [adjustmentValue, setAdjustmentValue] = useState('560.00');

  const loadProducts = async () => {
    setLoading(true);
    try {
      const data = await productService.list();
      setProducts(data);
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProducts();
  }, []);

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    try {
      await productService.create({
        name: productForm.name,
        sku: productForm.sku,
        description: productForm.description,
        is_active: true,
        variants: [
          {
            name: productForm.variant_name,
            sku: `${productForm.sku}-STD`,
            unit_price: parseFloat(productForm.base_price) || 0,
            currency: 'USD',
            is_active: true,
          },
        ],
      });
      setIsProductModalOpen(false);
      loadProducts();
    } catch (err) {
      alert(err.message || 'Error creating product');
    }
  };

  const handleAddVariant = async (e) => {
    e.preventDefault();
    if (!selectedProduct) return;
    try {
      await productService.addVariant(selectedProduct.id, {
        name: variantForm.name,
        sku: variantForm.sku,
        unit_price: parseFloat(variantForm.unit_price) || 0,
        currency: 'USD',
        is_active: true,
      });
      setIsVariantModalOpen(false);
      loadProducts();
    } catch (err) {
      alert(err.message || 'Error adding variant');
    }
  };

  const handleAdjustPrice = async (e) => {
    e.preventDefault();
    if (!selectedProduct || !selectedVariant) return;
    try {
      await productService.adjustVariantPrice(
        selectedProduct.id,
        selectedVariant.id,
        parseFloat(adjustmentValue) || 0
      );
      setIsAdjustModalOpen(false);
      loadProducts();
    } catch (err) {
      alert(err.message || 'Error adjusting price');
    }
  };

  const handleDeleteProduct = async (id) => {
    if (!window.confirm('Delete product and all its variants?')) return;
    try {
      await productService.delete(id);
      loadProducts();
    } catch (err) {
      alert(err.message || 'Error deleting product');
    }
  };

  const columns = [
    {
      header: 'Product Details',
      accessor: 'name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Package size={16} color="var(--primary)" />
            {row.name}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{row.description}</div>
        </div>
      ),
    },
    {
      header: 'SKU',
      accessor: 'sku',
      render: (row) => <span style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{row.sku || '—'}</span>,
    },
    {
      header: 'Variants & Prices',
      accessor: 'variants',
      render: (row) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {(row.variants || []).map((v) => (
            <div
              key={v.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.825rem',
                background: 'var(--bg-subtle)',
                padding: '0.2rem 0.5rem',
                borderRadius: 'var(--radius-sm)',
                width: 'fit-content',
              }}
            >
              <Tag size={12} color="var(--primary)" />
              <span style={{ fontWeight: 500 }}>{v.name}:</span>
              <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                ${Number(v.unit_price).toFixed(2)}
              </span>
              <button
                className="btn-icon"
                style={{ width: 22, height: 22, padding: 0 }}
                title="Adjust Price"
                onClick={() => {
                  setSelectedProduct(row);
                  setSelectedVariant(v);
                  setIsAdjustModalOpen(true);
                }}
              >
                <SlidersHorizontal size={12} />
              </button>
            </div>
          ))}
        </div>
      ),
    },
    {
      header: 'Actions',
      width: '140px',
      align: 'right',
      render: (row) => (
        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
          <button
            className="btn btn-outline"
            style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
            onClick={() => {
              setSelectedProduct(row);
              setVariantForm({
                name: '',
                sku: `${row.sku || 'PROD'}-VAR`,
                unit_price: '100.00',
                currency: 'USD',
              });
              setIsVariantModalOpen(true);
            }}
          >
            + Variant
          </button>
          {isAdmin && (
            <button
              className="btn-icon"
              style={{ color: 'var(--danger)' }}
              onClick={() => handleDeleteProduct(row.id)}
              title="Delete Product"
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
          <h1 className="page-title">Products & Variants</h1>
          <p className="page-subtitle">Configure software products, variant pricing, and optional add-ons.</p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => {
            setProductForm({
              name: '',
              sku: `BL-${Date.now().toString().slice(-4)}`,
              description: '',
              base_price: '199.00',
              variant_name: 'Standard Edition',
            });
            setIsProductModalOpen(true);
          }}
        >
          <Plus size={16} /> New Product
        </button>
      </div>

      <DataTable
        columns={columns}
        data={products}
        loading={loading}
        searchPlaceholder="Search products by name or SKU..."
        searchField="name"
      />

      {/* New Product Modal */}
      <Modal
        isOpen={isProductModalOpen}
        onClose={() => setIsProductModalOpen(false)}
        title="Add New Software Product"
      >
        <form onSubmit={handleCreateProduct} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Product Name *</label>
            <input
              className="form-input"
              value={productForm.name}
              onChange={(e) => setProductForm({ ...productForm, name: e.target.value })}
              placeholder="e.g. Automated Bank Feeds"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Product SKU</label>
              <input
                className="form-input"
                value={productForm.sku}
                onChange={(e) => setProductForm({ ...productForm, sku: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Base Sales Price ($)</label>
              <input
                type="number"
                step="0.01"
                className="form-input"
                value={productForm.base_price}
                onChange={(e) => setProductForm({ ...productForm, base_price: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Initial Variant Name</label>
            <input
              className="form-input"
              value={productForm.variant_name}
              onChange={(e) => setProductForm({ ...productForm, variant_name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description & Notes</label>
            <textarea
              className="form-textarea"
              rows={3}
              value={productForm.description}
              onChange={(e) => setProductForm({ ...productForm, description: e.target.value })}
              placeholder="Features, sales terms, and technical specifications"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsProductModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Product
            </button>
          </div>
        </form>
      </Modal>

      {/* Add Variant Modal */}
      <Modal
        isOpen={isVariantModalOpen}
        onClose={() => setIsVariantModalOpen(false)}
        title={`Add Variant to ${selectedProduct?.name}`}
      >
        <form onSubmit={handleAddVariant} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Variant Name *</label>
            <input
              className="form-input"
              value={variantForm.name}
              onChange={(e) => setVariantForm({ ...variantForm, name: e.target.value })}
              placeholder="e.g. Odoo Brand Edition"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Variant SKU</label>
              <input
                className="form-input"
                value={variantForm.sku}
                onChange={(e) => setVariantForm({ ...variantForm, sku: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Unit Price ($)</label>
              <input
                type="number"
                step="0.01"
                className="form-input"
                value={variantForm.unit_price}
                onChange={(e) => setVariantForm({ ...variantForm, unit_price: e.target.value })}
                required
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsVariantModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Add Variant
            </button>
          </div>
        </form>
      </Modal>

      {/* Price Adjustment Modal */}
      <Modal
        isOpen={isAdjustModalOpen}
        onClose={() => setIsAdjustModalOpen(false)}
        title={`Adjust Price: ${selectedVariant?.name}`}
      >
        <form onSubmit={handleAdjustPrice} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Current Unit Price:</p>
            <p style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              ${Number(selectedVariant?.unit_price || 0).toFixed(2)}
            </p>
          </div>

          <div className="form-group">
            <label className="form-label">Price Adjustment ($) *</label>
            <input
              type="number"
              step="0.01"
              className="form-input"
              value={adjustmentValue}
              onChange={(e) => setAdjustmentValue(e.target.value)}
              placeholder="e.g. 560.00 to add, or -20.00 to discount"
              required
            />
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Example from Brightloop spec: Choosing the Odoo brand adds +560.00 to the price.
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsAdjustModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Apply Price Adjustment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
