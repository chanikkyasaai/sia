import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Plus, Search, Receipt, Calendar, DollarSign, Tag, Edit2, Trash2, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { expenseApi } from '../../api/expenseApi';
import { ExpenseResponse } from '../../api/types';
import { useApi } from '../../hooks/useApi';

interface ExpenseFormData {
  amount: string;
  type: string;
  note: string;
  occurred_at: string;
  source: string;
}

const initialFormData: ExpenseFormData = {
  amount: '',
  type: 'expense',
  note: '',
  occurred_at: new Date().toISOString().slice(0, 16),
  source: 'manual',
};

export default function ExpensesPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedExpense, setSelectedExpense] = useState<ExpenseResponse | null>(null);
  const [expenses, setExpenses] = useState<ExpenseResponse[]>([]);
  const [formData, setFormData] = useState<ExpenseFormData>(initialFormData);

  // API hooks
  const {
    data: fetchedExpenses,
    loading: loadingExpenses,
    error: fetchError,
    execute: fetchExpenses,
  } = useApi(expenseApi.getAll);

  const {
    loading: creatingExpense,
    error: createError,
    execute: createExpense,
  } = useApi(expenseApi.create);

  // Load expenses on component mount
  useEffect(() => {
    fetchExpenses();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update local state when data is fetched
  useEffect(() => {
    if (fetchedExpenses) {
      console.log('Setting expenses state:', fetchedExpenses);
      setExpenses(fetchedExpenses);
    }
  }, [fetchedExpenses]);

  const filteredExpenses = expenses.filter(exp => {
    if (!searchQuery) return true; // Show all if no search query
    return exp.note?.toLowerCase().includes(searchQuery.toLowerCase()) || 
           exp.type?.toLowerCase().includes(searchQuery.toLowerCase());
  });

  console.log('Current expenses state:', expenses);
  console.log('First expense object:', expenses[0]);
  console.log('Filtered expenses:', filteredExpenses);
  console.log('Search query:', searchQuery);

  const handleFormChange = (field: keyof ExpenseFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData(initialFormData);
  };

  const handleSubmitExpense = async () => {
    try {
      const expenseData = {
        amount: parseFloat(formData.amount),
        type: formData.type,
        note: formData.note,
        occurred_at: formData.occurred_at,
        source: formData.source,
      };
      console.log('Creating expense:', expenseData);
      const created = await createExpense(expenseData);
      console.log('Expense created:', created);
      
      const refreshed = await fetchExpenses();
      console.log('Expenses refreshed:', refreshed);
      
      setShowAddModal(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create expense:', error);
    }
  };

  const isFormValid = formData.note.trim() && formData.type && formData.amount;

  const totalExpenses = expenses.reduce((sum, exp) => sum + parseFloat(exp.amount || '0'), 0);
  const todayExpenses = expenses.filter(exp => {
    const expDate = new Date(exp.occurred_at).toDateString();
    const today = new Date().toDateString();
    return expDate === today;
  }).reduce((sum, exp) => sum + parseFloat(exp.amount || '0'), 0);

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
      {/* Header */}
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
              <h1 className="text-display text-[#14213D] text-xl font-bold">Expenses</h1>
              <p className="text-caption text-gray-600 text-sm">{expenses.length} transactions</p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search expenses..."
              className="w-full pl-12 pr-4 py-3 rounded-2xl bg-gray-50 border border-gray-200 text-body text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="px-6 py-4 grid grid-cols-2 gap-3">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-br from-red-500 to-red-600 rounded-2xl p-4 shadow-lg"
        >
          <p className="text-caption text-white/80 text-xs mb-1">Total Expenses</p>
          <p className="text-display text-white text-2xl font-bold">₹{(totalExpenses / 1000).toFixed(1)}k</p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-4 shadow-lg"
        >
          <p className="text-caption text-white/80 text-xs mb-1">Today</p>
          <p className="text-display text-white text-2xl font-bold">₹{todayExpenses}</p>
        </motion.div>
      </div>

      {/* Expenses List */}
      <div className="px-6 py-2 space-y-3">
        {loadingExpenses ? (
          <div className="text-center py-12">
            <Loader2 size={32} className="animate-spin text-red-500 mx-auto" />
            <p className="text-body text-gray-500 mt-4">Loading expenses...</p>
          </div>
        ) : fetchError ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center">
            <p className="text-red-800 text-sm">{fetchError}</p>
            <button onClick={() => fetchExpenses()} className="mt-2 text-red-600 font-medium text-sm">
              Retry
            </button>
          </div>
        ) : filteredExpenses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-body text-gray-500">No expenses found</p>
          </div>
        ) : (
          filteredExpenses.map((expense, index) => (
          <motion.div
            key={expense.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-white rounded-2xl p-4 shadow-md border border-gray-100"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
                    <Receipt size={20} className="text-red-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-heading text-[#14213D] font-bold text-base">
                      {expense.note || 'Expense'}
                    </h3>
                    <div className="flex items-center gap-2 text-caption text-gray-500 text-xs mt-0.5">
                      <Calendar size={12} />
                      <span>{formatDate(expense.occurred_at)}</span>
                      <span>•</span>
                      <span>{formatTime(expense.occurred_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <p className="text-heading text-red-600 font-bold text-lg">
                  -₹{parseFloat(expense.amount || '0').toLocaleString('en-IN')}
                </p>
                <div className="flex gap-2">
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      setSelectedExpense(expense);
                      setShowEditModal(true);
                    }}
                    className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center"
                  >
                    <Edit2 size={14} className="text-blue-600" />
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      setSelectedExpense(expense);
                      setShowDeleteModal(true);
                    }}
                    className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center"
                  >
                    <Trash2 size={14} className="text-red-600" />
                  </motion.button>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {expense.source === 'voice' && (
                <div className="flex items-center gap-1.5 bg-blue-50 px-3 py-1.5 rounded-full">
                  <Tag size={12} className="text-blue-600" />
                  <span className="text-caption text-xs text-blue-700 font-medium">
                    Voice Added
                  </span>
                </div>
              )}
              <div className="flex items-center gap-1.5 bg-gray-100 px-3 py-1.5 rounded-full">
                <DollarSign size={12} className="text-gray-600" />
                <span className="text-caption text-xs text-gray-700 font-medium">
                  {expense.type}
                </span>
              </div>
            </div>
          </motion.div>
        )))
        }
      </div>

      {/* Floating Add Button */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: 'spring', stiffness: 300 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowAddModal(true)}
        className="fixed bottom-28 right-6 w-16 h-16 bg-gradient-to-br from-red-500 to-red-600 rounded-full shadow-2xl flex items-center justify-center z-40"
      >
        <Plus size={28} className="text-white" strokeWidth={3} />
      </motion.button>

      {/* Add Modal */}
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
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Add New Expense</h2>
              
              {createError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-red-800 text-sm">{createError}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Amount <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                    <input
                      type="number"
                      value={formData.amount}
                      onChange={(e) => handleFormChange('amount', e.target.value)}
                      placeholder="0"
                      className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Type <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.type}
                    onChange={(e) => handleFormChange('type', e.target.value)}
                    placeholder="e.g., Rent, Utilities, etc."
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Note <span className="text-red-500">*</span>
                  </label>
                  <textarea
                    value={formData.note}
                    onChange={(e) => handleFormChange('note', e.target.value)}
                    placeholder="Enter expense details"
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Date & Time</label>
                  <input
                    type="datetime-local"
                    value={formData.occurred_at}
                    onChange={(e) => handleFormChange('occurred_at', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSubmitExpense}
                  disabled={!isFormValid || creatingExpense}
                  className={`w-full py-4 rounded-2xl shadow-lg font-bold transition-all ${
                    isFormValid && !creatingExpense
                      ? 'bg-gradient-to-r from-red-500 to-red-600 text-white'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {creatingExpense ? (
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 size={20} className="animate-spin" />
                      <span>Adding...</span>
                    </div>
                  ) : (
                    'Add Expense'
                  )}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Modal */}
      <AnimatePresence>
        {showEditModal && selectedExpense && (
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
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Edit Expense</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Amount</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
                    <input
                      type="number"
                      defaultValue={selectedExpense.amount}
                      placeholder="0"
                      className="w-full pl-10 pr-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-red-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Description</label>
                  <textarea
                    defaultValue={selectedExpense.note || ''}
                    placeholder="What was this expense for?"
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
                  />
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  className="w-full py-4 bg-gradient-to-r from-red-500 to-red-600 text-white font-bold rounded-2xl shadow-lg"
                >
                  Update Expense
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {showDeleteModal && selectedExpense && (
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
              <h2 className="text-display text-[#14213D] text-xl font-bold text-center mb-2">Delete Expense?</h2>
              <p className="text-body text-gray-600 text-sm text-center mb-6">
                Are you sure you want to delete this expense? This action cannot be undone.
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
