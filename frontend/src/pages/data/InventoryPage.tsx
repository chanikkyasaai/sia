import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Plus, Search, Package, AlertTriangle, TrendingDown, Edit2, Trash2, Loader2, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { inventoryApi, ProductWithInventory } from '../../api/inventoryApi';
import { useApi } from '../../hooks/useApi';

interface InventoryFormData {
  name: string;
  unit: string;
  quantity_on_hand: string;
  low_stock_threshold: string;
  avg_cost_price: string;
  avg_sale_price: string;
  is_active: boolean;
}

const initialFormData: InventoryFormData = {
  name: '',
  unit: '',
  quantity_on_hand: '',
  low_stock_threshold: '',
  avg_cost_price: '',
  avg_sale_price: '',
  is_active: true,
};

export default function InventoryPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<ProductWithInventory | null>(null);
  const [inventory, setInventory] = useState<ProductWithInventory[]>([]);
  const [formData, setFormData] = useState<InventoryFormData>(initialFormData);

  // API hooks
  const {
    data: fetchedInventory,
    loading: loadingInventory,
    error: fetchError,
    execute: fetchInventory,
  } = useApi(inventoryApi.getAll);

  const {
    loading: creatingItem,
    error: createError,
    execute: createItem,
  } = useApi(inventoryApi.createWithInventory);

  // Load inventory on component mount
  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  // Update local inventory state when API data changes
  useEffect(() => {
    if (fetchedInventory) {
      setInventory(fetchedInventory);
    }
  }, [fetchedInventory]);

  const filteredInventory = inventory.filter(item =>
    (item.name?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
    (item.unit?.toLowerCase() || '').includes(searchQuery.toLowerCase())
  );

  const lowStockItems = inventory.filter(item =>
    item.low_stock_threshold && 
    item.quantity_on_hand !== undefined && 
    item.quantity_on_hand < item.low_stock_threshold
  );

  const totalValue = inventory.reduce((sum, item) =>
    sum + ((item.quantity_on_hand || 0) * (item.avg_cost_price || 0)), 0
  );

  const isLowStock = (item: ProductWithInventory) => {
    return item.low_stock_threshold && 
           item.quantity_on_hand !== undefined && 
           item.quantity_on_hand < item.low_stock_threshold;
  };

  const handleFormChange = (field: keyof InventoryFormData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData(initialFormData);
  };

  const handleSubmitItem = async () => {
    try {
      const itemData = {
        name: formData.name.trim(),
        unit: formData.unit.trim(),
        low_stock_threshold: formData.low_stock_threshold ? parseInt(formData.low_stock_threshold) : null,
        avg_cost_price: formData.avg_cost_price ? parseFloat(formData.avg_cost_price) : null,
        avg_sale_price: formData.avg_sale_price ? parseFloat(formData.avg_sale_price) : null,
        is_active: formData.is_active,
      };

      const quantityOnHand = formData.quantity_on_hand ? parseInt(formData.quantity_on_hand) : 0;

      console.log('Creating product with data:', itemData, 'quantity:', quantityOnHand);
      await createItem(itemData, quantityOnHand);
      
      // Refresh the inventory list
      await fetchInventory();
      
      // Close modal and reset form
      setShowAddModal(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create inventory item:', error);
      console.error('Error details:', JSON.stringify(error, null, 2));
    }
  };

  const isFormValid = formData.name.trim() && formData.unit.trim();

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white pb-32">
      <div className="bg-white border-b border-gray-200 sticky top-0 z-30">
        <div className="px-6 py-4">
          <div className="flex items-center gap-4 mb-4">
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => navigate('/data')}
              className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center"
            >
              <ArrowLeft size={20} className="text-gray-700" />
            </motion.button>
            <div>
              <h1 className="text-display text-[#14213D] text-xl font-bold">Inventory</h1>
              <p className="text-caption text-gray-600 text-sm">
                {loadingInventory ? 'Loading...' : `${inventory.length} products`}
              </p>
            </div>
          </div>

          <div className="relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search products..."
              className="w-full pl-12 pr-4 py-3 rounded-2xl bg-gray-50 border border-gray-200 text-body text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      </div>

      {/* Error Message */}
      {fetchError && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
          <AlertCircle size={20} className="text-red-600" />
          <div>
            <p className="text-red-800 font-medium text-sm">Failed to load inventory</p>
            <p className="text-red-600 text-xs">{fetchError}</p>
          </div>
          <button
            onClick={() => fetchInventory()}
            className="ml-auto px-3 py-1 bg-red-100 text-red-700 text-xs rounded-lg font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {!loadingInventory && inventory.length > 0 && (
      <div className="px-6 py-4 grid grid-cols-3 gap-3">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-4 shadow-lg"
        >
          <p className="text-caption text-white/80 text-xs mb-1">Products</p>
          <p className="text-display text-white text-2xl font-bold">{inventory.length}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-4 shadow-lg"
        >
          <p className="text-caption text-white/80 text-xs mb-1">Low Stock</p>
          <p className="text-display text-white text-2xl font-bold">{lowStockItems.length}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-4 shadow-lg"
        >
          <p className="text-caption text-white/80 text-xs mb-1">Value</p>
          <p className="text-display text-white text-lg font-bold">₹{(totalValue / 1000).toFixed(1)}k</p>
        </motion.div>
      </div>
      )}

      {lowStockItems.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-6 mb-4 bg-orange-50 border border-orange-200 rounded-2xl p-4"
        >
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="text-orange-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-heading text-orange-900 font-bold text-sm mb-1">
                Low Stock Alert
              </h3>
              <p className="text-caption text-orange-700 text-xs">
                {lowStockItems.length} {lowStockItems.length === 1 ? 'item needs' : 'items need'} restocking
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Loading State */}
      {loadingInventory && (
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3">
            <Loader2 size={24} className="text-green-600 animate-spin" />
            <span className="text-gray-600">Loading inventory...</span>
          </div>
        </div>
      )}

      {!loadingInventory && (
      <div className="px-6 py-2 space-y-3">
        {filteredInventory.map((item, index) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={`bg-white rounded-2xl p-4 shadow-md border-2 ${
              isLowStock(item) ? 'border-orange-200 bg-orange-50/30' : 'border-gray-100'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Package size={18} className="text-green-600" />
                  <h3 className="text-heading text-[#14213D] font-bold text-base">
                    {item.name}
                  </h3>
                </div>
                <p className="text-caption text-gray-500 text-xs mb-2">
                  Unit: {item.unit}
                </p>
                {item.avg_cost_price && item.avg_sale_price && (
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-caption text-gray-600">
                      Cost: ₹{item.avg_cost_price}/{item.unit}
                    </span>
                    <span className="text-caption text-green-600 font-medium">
                      Sale: ₹{item.avg_sale_price}/{item.unit}
                    </span>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={() => {
                    setSelectedProduct(item);
                    setShowEditModal(true);
                  }}
                  className="w-9 h-9 rounded-xl bg-green-50 flex items-center justify-center"
                >
                  <Edit2 size={16} className="text-green-600" />
                </motion.button>
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={() => {
                    setSelectedProduct(item);
                    setShowDeleteModal(true);
                  }}
                  className="w-9 h-9 rounded-xl bg-red-50 flex items-center justify-center"
                >
                  <Trash2 size={16} className="text-red-600" />
                </motion.button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isLowStock(item) && (
                  <div className="flex items-center gap-1.5 bg-orange-100 px-3 py-1.5 rounded-full">
                    <TrendingDown size={12} className="text-orange-600" />
                    <span className="text-caption text-xs text-orange-700 font-bold">
                      LOW STOCK
                    </span>
                  </div>
                )}
                {item.is_active && (
                  <div className="flex items-center gap-1.5 bg-green-100 px-3 py-1.5 rounded-full">
                    <span className="text-caption text-xs text-green-700 font-bold">
                      ACTIVE
                    </span>
                  </div>
                )}
              </div>
              {item.quantity_on_hand !== undefined && (
                <div className="bg-blue-100 px-4 py-2 rounded-xl">
                  <p className="text-caption text-xs text-blue-700 font-medium mb-0.5">
                    In Stock
                  </p>
                  <p className="text-heading text-blue-900 font-bold text-lg">
                    {item.quantity_on_hand} {item.unit}
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {filteredInventory.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <p className="text-body text-gray-500">No inventory items found</p>
          </motion.div>
        )}
      </div>
      )}

      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: 'spring', stiffness: 300 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowAddModal(true)}
        className="fixed bottom-28 right-6 w-16 h-16 bg-gradient-to-br from-green-500 to-green-600 rounded-full shadow-2xl flex items-center justify-center z-40"
      >
        <Plus size={28} className="text-white" strokeWidth={3} />
      </motion.button>

      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => {
              setShowAddModal(false);
              resetForm();
            }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-end"
          >
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full bg-white rounded-t-3xl p-6 pb-36 max-h-[85vh] overflow-y-auto"
            >
              <div className="w-12 h-1.5 bg-gray-300 rounded-full mx-auto mb-6" />
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Add New Product</h2>
              
              {createError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-red-800 text-sm">{createError}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Product Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleFormChange('name', e.target.value)}
                    placeholder="Enter product name"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Unit <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.unit}
                    onChange={(e) => handleFormChange('unit', e.target.value)}
                    placeholder="kg, litre, pieces, etc"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Initial Quantity <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={formData.quantity_on_hand}
                    onChange={(e) => handleFormChange('quantity_on_hand', e.target.value)}
                    placeholder="Enter initial stock quantity"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Cost Price (Optional)</label>
                    <input
                      type="number"
                      value={formData.avg_cost_price}
                      onChange={(e) => handleFormChange('avg_cost_price', e.target.value)}
                      placeholder="₹ 0"
                      className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Sale Price (Optional)</label>
                    <input
                      type="number"
                      value={formData.avg_sale_price}
                      onChange={(e) => handleFormChange('avg_sale_price', e.target.value)}
                      placeholder="₹ 0"
                      className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Low Stock Threshold (Optional)</label>
                  <input
                    type="number"
                    value={formData.low_stock_threshold}
                    onChange={(e) => handleFormChange('low_stock_threshold', e.target.value)}
                    placeholder="Notify when stock falls below..."
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSubmitItem}
                  disabled={!isFormValid || creatingItem}
                  className={`w-full py-4 rounded-2xl shadow-lg font-bold transition-all ${
                    isFormValid && !creatingItem
                      ? 'bg-gradient-to-r from-green-500 to-green-600 text-white'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {creatingItem ? (
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 size={20} className="animate-spin" />
                      <span>Adding...</span>
                    </div>
                  ) : (
                    'Add Product'
                  )}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showEditModal && selectedProduct && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowEditModal(false)}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-end"
          >
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 30 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full bg-white rounded-t-3xl p-6 pb-36 max-h-[85vh] overflow-y-auto"
            >
              <div className="w-12 h-1.5 bg-gray-300 rounded-full mx-auto mb-6" />
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Edit Product</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Product Name</label>
                  <input
                    type="text"
                    defaultValue={selectedProduct.name}
                    placeholder="Enter product name"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Unit</label>
                  <input
                    type="text"
                    defaultValue={selectedProduct.unit}
                    placeholder="kg, litre, etc"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Cost Price</label>
                    <input
                      type="number"
                      defaultValue={selectedProduct.avg_cost_price || 0}
                      placeholder="₹ 0"
                      className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Sale Price</label>
                    <input
                      type="number"
                      defaultValue={selectedProduct.avg_sale_price || 0}
                      placeholder="₹ 0"
                      className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Low Stock Threshold</label>
                  <input
                    type="number"
                    defaultValue={selectedProduct.low_stock_threshold || 0}
                    placeholder="Notify when stock falls below..."
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  className="w-full py-4 bg-gradient-to-r from-green-500 to-green-600 text-white font-bold rounded-2xl shadow-lg"
                >
                  Update Product
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showDeleteModal && selectedProduct && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowDeleteModal(false)}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[60] flex items-center justify-center p-6"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-3xl p-6 max-w-sm w-full shadow-2xl"
            >
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                <Trash2 size={24} className="text-red-600" />
              </div>
              <h2 className="text-display text-[#14213D] text-xl font-bold text-center mb-2">Delete Product?</h2>
              <p className="text-body text-gray-600 text-sm text-center mb-6">
                Are you sure you want to delete <span className="font-bold">{selectedProduct.name}</span>? This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowDeleteModal(false)}
                  className="flex-1 py-3 bg-gray-100 text-gray-700 font-bold rounded-xl"
                >
                  Cancel
                </motion.button>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    setShowDeleteModal(false);
                  }}
                  className="flex-1 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-bold rounded-xl shadow-lg"
                >
                  Delete
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
