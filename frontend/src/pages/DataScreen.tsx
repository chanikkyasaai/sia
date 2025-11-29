import { Users, Package, Receipt, ShoppingCart, ArrowRight, TrendingUp } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export default function DataScreen() {
  const dataCategories = [
    {
      icon: Users,
      label: 'Customers & Credit',
      color: '#2563EB',
      count: '24 Customers',
      highlight: '₹12.5k Pending',
    },
    {
      icon: Package,
      label: 'Inventory',
      color: '#22C55E',
      count: '156 Items',
      highlight: '3 Low Stock',
    },
    {
      icon: Receipt,
      label: 'Expenses',
      color: '#EF4444',
      count: 'This Month',
      highlight: '₹12,850',
    },
    {
      icon: ShoppingCart,
      label: 'Sales',
      color: '#FCA311',
      count: 'Today',
      highlight: '12 Sales',
    },
  ];

  const navigate = useNavigate();

  const categoryPaths = ['/data/customers', '/data/inventory', '/data/expenses', '/data/sales'];

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white p-6 pt-8 pb-32">
      <div className="mb-8">
        <h1 className="font-['Poppins'] font-bold text-[#14213D] text-2xl mb-1">
          Business Data
        </h1>
        <p className="font-['Inter'] text-sm text-gray-600">
          Manage all your business information
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {dataCategories.map((category, index) => (
          <motion.button
            key={index}
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: index * 0.1, type: 'spring', stiffness: 100 }}
            whileHover={{ scale: 1.05, y: -5 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => navigate(categoryPaths[index])}
            className="relative bg-white rounded-3xl p-6 shadow-lg hover:shadow-2xl transition-all border border-gray-100 overflow-hidden group"
          >
            {/* Animated gradient background on hover */}
            <motion.div
              className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
              style={{
                background: `linear-gradient(135deg, ${category.color}10 0%, ${category.color}05 100%)`,
              }}
            />

            <div className="relative z-10">
              <div className="flex items-start justify-between mb-4">
                <motion.div
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.6 }}
                  className="w-14 h-14 rounded-2xl flex items-center justify-center shadow-md"
                  style={{
                    background: `linear-gradient(135deg, ${category.color} 0%, ${category.color}dd 100%)`,
                  }}
                >
                  <category.icon size={28} className="text-white" strokeWidth={2.5} />
                </motion.div>
                <motion.div
                  initial={{ opacity: 0 }}
                  whileHover={{ opacity: 1, x: 5 }}
                  transition={{ duration: 0.2 }}
                >
                  <ArrowRight size={20} className="text-gray-400" />
                </motion.div>
              </div>

              <h3 className="font-['Poppins'] font-semibold text-[#14213D] text-sm mb-2 leading-tight">
                {category.label}
              </h3>

              <div className="space-y-1">
                <p className="font-['Inter'] text-xs text-gray-500">{category.count}</p>
                <p className="font-['Inter'] font-bold text-lg" style={{ color: category.color }}>
                  {category.highlight}
                </p>
              </div>
            </div>

            {/* Corner accent */}
            <div
              className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full opacity-10"
              style={{ backgroundColor: category.color }}
            />
          </motion.button>
        ))}
      </div>

      {/* Quick Stats Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="bg-gradient-to-br from-[#14213D] to-[#1a2a4d] rounded-3xl p-6 shadow-xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-32 h-32 bg-[#FCA311]/20 rounded-full -translate-y-1/2 translate-x-1/2 blur-2xl" />

        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-full bg-[#22C55E]/20 flex items-center justify-center">
              <TrendingUp size={16} className="text-[#22C55E]" />
            </div>
            <h3 className="font-['Poppins'] font-semibold text-white text-base">
              Quick Overview
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="font-['Inter'] text-xs text-white/60 mb-1">Total Items</p>
              <p className="font-['Inter'] font-bold text-white text-xl">156</p>
            </div>
            <div>
              <p className="font-['Inter'] text-xs text-white/60 mb-1">Total Value</p>
              <p className="font-['Inter'] font-bold text-white text-xl">₹45k</p>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Helpful tip */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        className="mt-6 bg-blue-50 border border-blue-100 rounded-2xl p-4"
      >
        <p className="font-['Inter'] text-sm text-blue-900 leading-relaxed">
          <span className="font-semibold">💡 Tip:</span> Tap any category to view detailed records and manage your data efficiently.
        </p>
      </motion.div>
    </div>
  );
}
