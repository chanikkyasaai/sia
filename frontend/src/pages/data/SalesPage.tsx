import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Plus, Search, ShoppingCart, Calendar, Package, Tag, User, Edit2, Trash2, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { salesApi } from '../../api/salesApi';
import { TransactionResponse } from '../../api/types';
import { useApi } from '../../hooks/useApi';

export default function SalesPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedSale, setSelectedSale] = useState<TransactionResponse | null>(null);
  const [sales, setSales] = useState<TransactionResponse[]>([]);

  // API hooks
  const {
    data: fetchedSales,
    loading: loadingSales,
    error: fetchError,
    execute: fetchSales,
  } = useApi(salesApi.getAll);

  // Load sales on component mount
  useEffect(() => {
    fetchSales();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update local state when data is fetched
  useEffect(() => {
    if (fetchedSales) {
      console.log('Setting sales state:', fetchedSales);
      setSales(fetchedSales);
    }
  }, [fetchedSales]);

  const filteredSales = sales.filter(sale => {
    if (!searchQuery) return true;
    const matchesSearch =
      sale.customer.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sale.product.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sale.note?.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesSearch;
  });

  const totalSales = sales.reduce((sum, s) => sum + s.amount, 0);
  const todaySales = sales.filter(s => {
    const saleDate = new Date(s.created_at).toDateString();
    const today = new Date().toDateString();
    return saleDate === today;
  }).length;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  };

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
              <h1 className="text-display text-[#14213D] text-xl font-bold">Sales</h1>
              <p className="text-caption text-gray-600 text-sm">{sales.length} transactions</p>
            </div>
          </div>

          <div className="relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search sales..."
              className="w-full pl-12 pr-4 py-3 rounded-2xl bg-gray-50 border border-gray-200 text-body text-sm focus:outline-none focus:ring-2 focus:ring-[#FCA311] focus:border-transparent transition-all"
            />
          </div>
        </div>
      </div>

      <div className="px-6 py-4 grid grid-cols-3 gap-3">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-[#FCA311] to-orange-600 rounded-2xl p-4 shadow-lg"
        >
          <p className="text-caption text-white/80 text-xs mb-1">Today</p>
          <p className="text-display text-white text-2xl font-bold">{todaySales}</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-4 col-span-2 shadow-lg"
        >
          <p className="text-caption text-white/80 text-xs mb-1">Total Revenue</p>
          <p className="text-display text-white text-2xl font-bold">₹{(totalSales / 1000).toFixed(1)}k</p>
        </motion.div>
      </div>

      <div className="px-6 py-2 space-y-3">
        {filteredSales.map((sale, index) => (
          <motion.div
            key={sale.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-white rounded-2xl p-4 shadow-md border-2 border-green-100"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-green-100 flex items-center justify-center flex-shrink-0">
                    <ShoppingCart size={20} className="text-green-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-heading text-[#14213D] font-bold text-base">
                      {sale.product?.name || 'Product'}
                    </h3>
                    <div className="flex items-center gap-2 text-caption text-gray-500 text-xs mt-0.5">
                      <Calendar size={12} />
                      <span>{formatDate(sale.created_at)}</span>
                      <span>•</span>
                      <span>{formatTime(sale.created_at)}</span>
                    </div>
                  </div>
                </div>

                {sale.customer && (
                  <div className="flex items-center gap-2 text-body text-gray-600 text-sm mb-2">
                    <User size={14} />
                    <span>{sale.customer.name}</span>
                  </div>
                )}

                {sale.note && (
                  <p className="text-caption text-gray-500 text-xs mb-2">{sale.note}</p>
                )}
              </div>

              <div className="flex flex-col items-end gap-2">
                <p className="text-heading font-bold text-lg text-green-600">
                  +₹{sale.amount.toLocaleString('en-IN')}
                </p>
                {sale.quantity && (
                  <p className="text-caption text-gray-500 text-xs">
                    Qty: {sale.quantity}
                  </p>
                )}
                <div className="flex gap-2 mt-1">
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      setSelectedSale(sale);
                      setShowEditModal(true);
                    }}
                    className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center"
                  >
                    <Edit2 size={14} className="text-blue-600" />
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      setSelectedSale(sale);
                      setShowDeleteModal(true);
                    }}
                    className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center"
                  >
                    <Trash2 size={14} className="text-red-600" />
                  </motion.button>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-1.5 bg-green-50 px-3 py-1.5 rounded-full">
                <Package size={12} className="text-green-600" />
                <span className="text-caption text-xs text-green-700 font-medium">SALE</span>
              </div>
              {sale.source === 'voice' && (
                <div className="flex items-center gap-1.5 bg-orange-50 px-3 py-1.5 rounded-full">
                  <Tag size={12} className="text-orange-600" />
                  <span className="text-caption text-xs text-orange-700 font-medium">Voice Added</span>
                </div>
              )}
            </div>
          </motion.div>
        ))}

        {filteredSales.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <p className="text-body text-gray-500">No sales found</p>
          </motion.div>
        )}
      </div>

      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: 'spring', stiffness: 300 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowAddModal(true)}
        className="fixed bottom-28 right-6 w-16 h-16 bg-gradient-to-br from-[#FCA311] to-orange-600 rounded-full shadow-2xl flex items-center justify-center z-40"
      >
        <Plus size={28} className="text-white" strokeWidth={3} />
      </motion.button>

      <AnimatePresence>
        {showAddModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAddModal(false)}
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
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Add New Sale</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Product</label>
                  <input
                    type="text"
                    placeholder="Select or enter product"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Quantity</label>
                    <input
                      type="number"
                      placeholder="0"
                      className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                    />
                  </div>
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Amount</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                      <input
                        type="number"
                        placeholder="0"
                        className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Customer (Optional)</label>
                  <input
                    type="text"
                    placeholder="Select customer"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Note (Optional)</label>
                  <textarea
                    placeholder="Add any additional notes..."
                    rows={2}
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311] resize-none"
                  />
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  className="w-full py-4 bg-gradient-to-r from-[#FCA311] to-orange-600 text-white font-bold rounded-2xl shadow-lg"
                >
                  Add Sale
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showEditModal && selectedSale && (
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
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Edit Sale</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Product</label>
                  <input
                    type="text"
                    defaultValue={selectedSale.product.name || ''}
                    placeholder="Select or enter product"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Quantity</label>
                    <input
                      type="number"
                      defaultValue={selectedSale.quantity || 0}
                      placeholder="0"
                      className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                    />
                  </div>
                  <div>
                    <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Amount</label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                      <input
                        type="number"
                        defaultValue={selectedSale.amount}
                        placeholder="0"
                        className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Customer (Optional)</label>
                  <input
                    type="text"
                    defaultValue={selectedSale.customer.name || ''}
                    placeholder="Select customer"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311]"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Note (Optional)</label>
                  <textarea
                    defaultValue={selectedSale.note || ''}
                    placeholder="Add any additional notes..."
                    rows={2}
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-[#FCA311] resize-none"
                  />
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  className="w-full py-4 bg-gradient-to-r from-[#FCA311] to-orange-600 text-white font-bold rounded-2xl shadow-lg"
                >
                  Update Sale
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showDeleteModal && selectedSale && (
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
              <h2 className="text-display text-[#14213D] text-xl font-bold text-center mb-2">Delete Sale?</h2>
              <p className="text-body text-gray-600 text-sm text-center mb-6">
                Are you sure you want to delete this sale record? This action cannot be undone.
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
