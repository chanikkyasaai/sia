import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Plus, Search, Phone, AlertCircle, TrendingUp, Edit2, Trash2, IndianRupee, Loader2, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { customerApi } from '../../api/customerApi';
import { CustomerResponse } from '../../api/types';
import { useApi } from '../../hooks/useApi';

interface CustomerFormData {
  name: string;
  phone: string;
  info: string;
  risk_level: string;
  creditType: 'owes_business' | 'business_owes' | 'none';
  creditAmount: string;
  avg_delay_days: string;
}

const initialFormData: CustomerFormData = {
  name: '',
  phone: '',
  info: '',
  risk_level: 'low',
  creditType: 'none',
  creditAmount: '',
  avg_delay_days: '',
};

export default function CustomersPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerResponse | null>(null);
  const [customers, setCustomers] = useState<CustomerResponse[]>([]);
  const [formData, setFormData] = useState<CustomerFormData>(initialFormData);

  // API hooks
  const {
    data: fetchedCustomers,
    loading: loadingCustomers,
    error: fetchError,
    execute: fetchCustomers,
  } = useApi(customerApi.getAll);

  const {
    loading: creatingCustomer,
    error: createError,
    execute: createCustomer,
  } = useApi(customerApi.create);

  // Load customers on component mount
  useEffect(() => {
    fetchCustomers();
  }, [fetchCustomers]);

  // Update local customers state when API data changes
  useEffect(() => {
    if (fetchedCustomers) {
      setCustomers(fetchedCustomers);
    }
  }, [fetchedCustomers]);

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return '#22C55E';
      case 'medium': return '#FCA311';
      case 'high': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const filteredCustomers = customers.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.phone.includes(searchQuery)
  );

  const handleFormChange = (field: keyof CustomerFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData(initialFormData);
  };

  const handleSubmitCustomer = async () => {
    try {
      // Calculate credit value based on type
      let creditValue: number | null = null;
      if (formData.creditType !== 'none' && formData.creditAmount) {
        const amount = parseFloat(formData.creditAmount);
        if (!isNaN(amount)) {
          creditValue = formData.creditType === 'owes_business' ? -amount : amount;
        }
      }

      const customerData = {
        name: formData.name.trim(),
        phone: formData.phone.trim(),
        info: formData.info.trim() || null,
        risk_level: formData.risk_level,
        credit: creditValue,
        avg_delay_days: formData.avg_delay_days ? parseInt(formData.avg_delay_days) : null,
      };

      await createCustomer(customerData);
      
      // Refresh the customers list
      await fetchCustomers();
      
      // Close modal and reset form
      setShowAddModal(false);
      resetForm();
    } catch (error) {
      console.error('Failed to create customer:', error);
    }
  };

  const isFormValid = formData.name.trim() && formData.phone.trim();

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
              <h1 className="text-display text-[#14213D] text-xl font-bold">Customers</h1>
              <p className="text-caption text-gray-600 text-sm">
                {loadingCustomers ? 'Loading...' : `${customers.length} total customers`}
              </p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or phone..."
              className="w-full pl-12 pr-4 py-3 rounded-2xl bg-gray-50 border border-gray-200 text-body text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
        </div>
      </div>

      {/* Error Message */}
      {fetchError && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
          <AlertTriangle size={20} className="text-red-600" />
          <div>
            <p className="text-red-800 font-medium text-sm">Failed to load customers</p>
            <p className="text-red-600 text-xs">{fetchError}</p>
          </div>
          <button
            onClick={() => fetchCustomers()}
            className="ml-auto px-3 py-1 bg-red-100 text-red-700 text-xs rounded-lg font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {/* Stats Cards */}
      {!loadingCustomers && customers.length > 0 && (
        <div className="px-6 py-4 grid grid-cols-3 gap-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-4 shadow-lg"
          >
            <p className="text-caption text-white/80 text-xs mb-1">Total</p>
            <p className="text-display text-white text-2xl font-bold">{customers.length}</p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-4 shadow-lg"
          >
            <p className="text-caption text-white/80 text-xs mb-1">Low Risk</p>
            <p className="text-display text-white text-2xl font-bold">
              {customers.filter(c => c.risk_level === 'low').length}
            </p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-red-500 to-red-600 rounded-2xl p-4 shadow-lg"
          >
            <p className="text-caption text-white/80 text-xs mb-1">High Risk</p>
            <p className="text-display text-white text-2xl font-bold">
              {customers.filter(c => c.risk_level === 'high').length}
            </p>
          </motion.div>
        </div>
      )}

      {/* Loading State */}
      {loadingCustomers && (
        <div className="flex items-center justify-center py-20">
          <div className="flex items-center gap-3">
            <Loader2 size={24} className="text-blue-600 animate-spin" />
            <span className="text-gray-600">Loading customers...</span>
          </div>
        </div>
      )}

      {/* Customer List */}
      {!loadingCustomers && (
        <div className="px-6 py-2 space-y-3">
          {filteredCustomers.map((customer, index) => (
            <motion.div
              key={customer.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white rounded-2xl p-4 shadow-md border border-gray-100"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-heading text-[#14213D] font-bold text-base mb-1">
                    {customer.name}
                  </h3>
                  <div className="flex items-center gap-2 text-body text-gray-600 text-sm mb-2">
                    <Phone size={14} />
                    <span>{customer.phone}</span>
                  </div>
                  {customer.info && (
                    <div className="inline-flex items-center gap-1.5 bg-blue-50 px-2.5 py-1 rounded-full">
                      <span className="text-caption text-blue-700 text-xs font-medium">{customer.info}</span>
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      setSelectedCustomer(customer);
                      setShowEditModal(true);
                    }}
                    className="w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center"
                  >
                    <Edit2 size={16} className="text-blue-600" />
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => {
                      setSelectedCustomer(customer);
                      setShowDeleteModal(true);
                    }}
                    className="w-9 h-9 rounded-xl bg-red-50 flex items-center justify-center"
                  >
                    <Trash2 size={16} className="text-red-600" />
                  </motion.button>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <AlertCircle size={14} style={{ color: getRiskColor(customer.risk_level) }} />
                  <span className="text-caption text-xs font-bold" style={{ color: getRiskColor(customer.risk_level) }}>
                    {customer.risk_level.toUpperCase()} RISK
                  </span>
                </div>
                {customer.avg_delay_days !== null && customer.avg_delay_days !== undefined && (
                  <div className="flex items-center gap-1.5 bg-gray-50 px-3 py-1.5 rounded-full">
                    <TrendingUp size={12} className="text-gray-600" />
                    <span className="text-caption text-xs text-gray-700 font-medium">
                      {customer.avg_delay_days}d avg delay
                    </span>
                  </div>
                )}
                {customer.credit !== null && customer.credit !== undefined && (
                  <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full ${
                    customer.credit < 0 ? 'bg-red-50' : 'bg-green-50'
                  }`}>
                    <IndianRupee size={12} className={customer.credit < 0 ? 'text-red-600' : 'text-green-600'} />
                    <span className={`text-caption text-xs font-bold ${
                      customer.credit < 0 ? 'text-red-700' : 'text-green-700'
                    }`}>
                      {customer.credit < 0 ? 'Owes' : 'Has'} ₹{Math.abs(customer.credit).toLocaleString('en-IN')}
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}

          {filteredCustomers.length === 0 && !loadingCustomers && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-12"
            >
              <p className="text-body text-gray-500">
                {searchQuery ? 'No customers found matching your search' : 'No customers yet. Add your first customer!'}
              </p>
            </motion.div>
          )}
        </div>
      )}

      {/* Floating Add Button */}
      <motion.button
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, type: 'spring', stiffness: 300 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowAddModal(true)}
        className="fixed bottom-28 right-6 w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full shadow-2xl flex items-center justify-center z-40"
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
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Add New Customer</h2>
              
              {createError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-red-800 text-sm">{createError}</p>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleFormChange('name', e.target.value)}
                    placeholder="Enter customer name"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">
                    Phone <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => handleFormChange('phone', e.target.value)}
                    placeholder="+91 XXXXX XXXXX"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Risk Level</label>
                  <select
                    value={formData.risk_level}
                    onChange={(e) => handleFormChange('risk_level', e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="low">Low Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="high">High Risk</option>
                  </select>
                </div>
                
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Marker/Tag (Optional)</label>
                  <input
                    type="text"
                    value={formData.info}
                    onChange={(e) => handleFormChange('info', e.target.value)}
                    placeholder="e.g., Regular cust, VIP, Wholesale, New"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-caption text-gray-500 text-xs mt-1">Short tag to identify this customer</p>
                </div>

                {/* Credit Section */}
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-3">Credit Balance (Optional)</label>
                  
                  {/* Credit Type Radio Buttons */}
                  <div className="flex gap-2 mb-3">
                    <label className="flex-1">
                      <input
                        type="radio"
                        name="creditType"
                        value="none"
                        checked={formData.creditType === 'none'}
                        onChange={(e) => handleFormChange('creditType', e.target.value)}
                        className="sr-only"
                      />
                      <div className={`p-3 rounded-xl border-2 text-center cursor-pointer transition-all ${
                        formData.creditType === 'none' 
                          ? 'border-gray-400 bg-gray-50' 
                          : 'border-gray-200 bg-white'
                      }`}>
                        <span className="text-sm font-medium text-gray-700">No Credit</span>
                      </div>
                    </label>
                    
                    <label className="flex-1">
                      <input
                        type="radio"
                        name="creditType"
                        value="owes_business"
                        checked={formData.creditType === 'owes_business'}
                        onChange={(e) => handleFormChange('creditType', e.target.value)}
                        className="sr-only"
                      />
                      <div className={`p-3 rounded-xl border-2 text-center cursor-pointer transition-all ${
                        formData.creditType === 'owes_business' 
                          ? 'border-red-400 bg-red-50' 
                          : 'border-gray-200 bg-white'
                      }`}>
                        <span className="text-sm font-medium text-red-700">Customer Owes</span>
                      </div>
                    </label>
                    
                    <label className="flex-1">
                      <input
                        type="radio"
                        name="creditType"
                        value="business_owes"
                        checked={formData.creditType === 'business_owes'}
                        onChange={(e) => handleFormChange('creditType', e.target.value)}
                        className="sr-only"
                      />
                      <div className={`p-3 rounded-xl border-2 text-center cursor-pointer transition-all ${
                        formData.creditType === 'business_owes' 
                          ? 'border-green-400 bg-green-50' 
                          : 'border-gray-200 bg-white'
                      }`}>
                        <span className="text-sm font-medium text-green-700">You Owe</span>
                      </div>
                    </label>
                  </div>

                  {/* Credit Amount Input */}
                  {formData.creditType !== 'none' && (
                    <input
                      type="number"
                      value={formData.creditAmount}
                      onChange={(e) => handleFormChange('creditAmount', e.target.value)}
                      placeholder="Enter amount"
                      className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  )}
                </div>

                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Average Delay Days (Optional)</label>
                  <input
                    type="number"
                    value={formData.avg_delay_days}
                    onChange={(e) => handleFormChange('avg_delay_days', e.target.value)}
                    placeholder="Enter average payment delay in days"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSubmitCustomer}
                  disabled={!isFormValid || creatingCustomer}
                  className={`w-full py-4 rounded-2xl shadow-lg font-bold transition-all ${
                    isFormValid && !creatingCustomer
                      ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {creatingCustomer ? (
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 size={20} className="animate-spin" />
                      <span>Adding...</span>
                    </div>
                  ) : (
                    'Add Customer'
                  )}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Edit Modal */}
      <AnimatePresence>
        {showEditModal && selectedCustomer && (
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
              <h2 className="text-display text-[#14213D] text-xl font-bold mb-6">Edit Customer</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Name</label>
                  <input
                    type="text"
                    defaultValue={selectedCustomer.name}
                    placeholder="Enter customer name"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Phone</label>
                  <input
                    type="tel"
                    defaultValue={selectedCustomer.phone}
                    placeholder="+91 XXXXX XXXXX"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Risk Level</label>
                  <select defaultValue={selectedCustomer.risk_level} className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <option value="low">Low Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="high">High Risk</option>
                  </select>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Marker/Tag (Optional)</label>
                  <input
                    type="text"
                    defaultValue={selectedCustomer.info || ''}
                    placeholder="e.g., Regular cust, VIP, Wholesale, New"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-caption text-gray-500 text-xs mt-1">Short tag to identify this customer</p>
                </div>
                <div>
                  <label className="text-caption text-gray-700 text-sm font-medium block mb-2">Credit Balance (Optional)</label>
                  <input
                    type="number"
                    defaultValue={selectedCustomer.credit || 0}
                    placeholder="Enter amount (- if customer owes, + if customer has credit)"
                    className="w-full px-4 py-3 rounded-xl bg-gray-50 border border-gray-200 text-body focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-caption text-gray-500 text-xs mt-1">Negative = Customer owes, Positive = Customer has credit with you</p>
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  className="w-full py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-bold rounded-2xl shadow-lg"
                >
                  Update Customer
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {showDeleteModal && selectedCustomer && (
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
              <h2 className="text-display text-[#14213D] text-xl font-bold text-center mb-2">Delete Customer?</h2>
              <p className="text-body text-gray-600 text-sm text-center mb-6">
                Are you sure you want to delete <span className="font-bold">{selectedCustomer.name}</span>? This action cannot be undone.
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
