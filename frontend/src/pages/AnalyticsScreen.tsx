import { TrendingUp, AlertCircle, PackageX, TrendingDown, DollarSign, Users, ArrowRight, Clock, CheckCircle2, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

export default function AnalyticsScreen() {
  const profitData = [2100, 2800, 3200, 2900, 3500, 3800, 4250];
  const maxProfit = Math.max(...profitData);

  return (
    <div className="p-6 pt-8 pb-32 bg-gradient-to-b from-[#0a0118]/5 to-white">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-['Poppins'] font-bold text-[#14213D] text-2xl mb-1">
            Business Intelligence
          </h1>
          <p className="font-['Inter'] text-sm text-[#14213D]/60">
            AI-powered insights
          </p>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 bg-gradient-to-br from-[#14213D] to-[#1a2a4d] rounded-3xl p-6 shadow-xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-40 h-40 bg-[#FCA311]/20 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-full bg-[#22C55E]/20 flex items-center justify-center">
              <CheckCircle2 size={18} className="text-[#22C55E]" />
            </div>
            <p className="font-['Poppins'] font-semibold text-white text-sm">
              OVERALL HEALTH
            </p>
          </div>
          <h3 className="font-['Poppins'] font-bold text-white text-2xl mb-3">
            Your Business is Thriving
          </h3>
          <p className="font-['Inter'] text-sm text-white/80 leading-relaxed">
            Your business shows strong performance with consistent profit growth. Cashflow remains positive for the next 7 days, and revenue is up 18% compared to last week. All key metrics indicate healthy operations with no immediate concerns.
          </p>
        </div>
      </motion.div>

      <div className="mb-6">
        <h2 className="font-['Poppins'] font-semibold text-[#14213D] text-lg mb-4 flex items-center gap-2">
          <DollarSign size={20} className="text-[#FCA311]" />
          Financial Snapshot
        </h2>
        <div className="grid grid-cols-2 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="bg-gradient-to-br from-[#FCA311] to-[#e89510] rounded-2xl p-5 shadow-lg"
          >
            <div className="flex items-center justify-between mb-2">
              <TrendingUp size={20} className="text-white" />
              <span className="font-['Inter'] text-xs font-medium text-white bg-white/20 px-2 py-1 rounded-full">
                +18%
              </span>
            </div>
            <p className="font-['Inter'] text-xs text-white/70 mb-1">Today's Profit</p>
            <p className="font-['Inter'] font-bold text-2xl text-white">₹4,250</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-gradient-to-br from-[#14213D] to-[#1a2a4d] rounded-2xl p-5 shadow-lg"
          >
            <div className="flex items-center justify-between mb-2">
              <TrendingUp size={20} className="text-white" />
              <span className="font-['Inter'] text-xs font-medium text-white bg-white/20 px-2 py-1 rounded-full">
                Weekly
              </span>
            </div>
            <p className="font-['Inter'] text-xs text-white/70 mb-1">Revenue</p>
            <p className="font-['Inter'] font-bold text-2xl text-white">₹28,400</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl p-5 shadow-lg border-2 border-[#FCA311]/20"
          >
            <div className="flex items-center justify-between mb-2">
              <AlertCircle size={20} className="text-[#FCA311]" />
              <span className="font-['Inter'] text-xs font-medium text-[#FCA311] bg-[#FCA311]/10 px-2 py-1 rounded-full">
                Pending
              </span>
            </div>
            <p className="font-['Inter'] text-xs text-[#14213D]/60 mb-1">Udhaar Due</p>
            <p className="font-['Inter'] font-bold text-2xl text-[#14213D]">₹12,500</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-2xl p-5 shadow-lg border-2 border-[#14213D]/10"
          >
            <div className="flex items-center justify-between mb-2">
              <TrendingDown size={20} className="text-[#14213D]" />
              <span className="font-['Inter'] text-xs font-medium text-[#14213D]/70 bg-[#14213D]/10 px-2 py-1 rounded-full">
                Daily
              </span>
            </div>
            <p className="font-['Inter'] text-xs text-[#14213D]/60 mb-1">Expenses</p>
            <p className="font-['Inter'] font-bold text-2xl text-[#14213D]">₹1,850</p>
          </motion.div>
        </div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-4 bg-gradient-to-br from-[#14213D]/5 to-transparent rounded-2xl p-4 border border-[#14213D]/10"
        >
          <div className="flex gap-2 mb-2">
            <Sparkles size={16} className="text-[#FCA311] flex-shrink-0 mt-0.5" />
            <p className="font-['Inter'] text-sm text-[#14213D]/80 leading-relaxed">
              Your profit margins are excellent at 18%. Revenue streams are diversified, and daily expenses remain under control. Focus on collecting pending payments to further strengthen your cash position.
            </p>
          </div>
        </motion.div>
      </div>

      <div className="mb-6 bg-white rounded-3xl p-6 shadow-lg border border-[#14213D]/10">
        <h3 className="font-['Poppins'] font-semibold text-[#14213D] text-base mb-4">
          7-Day Profit Trend
        </h3>
        <div className="flex items-end justify-between gap-2 h-40 mb-3">
          {profitData.map((profit, index) => (
            <motion.div
              key={index}
              initial={{ height: 0 }}
              animate={{ height: `${(profit / maxProfit) * 100}%` }}
              transition={{ delay: index * 0.1, duration: 0.6, ease: 'easeOut' }}
              className="flex-1 bg-gradient-to-t from-[#FCA311] to-[#FCA311]/60 rounded-t-xl relative group min-w-0"
            >
              <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-[#14213D] text-white text-xs font-['Inter'] font-semibold px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap shadow-lg z-10">
                ₹{profit.toLocaleString('en-IN')}
              </div>
            </motion.div>
          ))}
        </div>
        <div className="flex justify-between">
          {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map((day, index) => (
            <span key={index} className="font-['Inter'] text-xs font-medium text-[#14213D]/50 flex-1 text-center">
              {day}
            </span>
          ))}
        </div>
        <div className="mt-4 bg-gradient-to-br from-[#14213D]/5 to-transparent rounded-2xl p-4 border border-[#14213D]/10">
          <div className="flex gap-2">
            <Sparkles size={16} className="text-[#FCA311] flex-shrink-0 mt-0.5" />
            <p className="font-['Inter'] text-sm text-[#14213D]/80 leading-relaxed">
              Steady upward trajectory over the week indicates growing business momentum. Weekend performance is particularly strong, suggesting high customer footfall on Saturdays and Sundays.
            </p>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <h2 className="font-['Poppins'] font-semibold text-[#14213D] text-lg mb-4 flex items-center gap-2">
          <AlertCircle size={20} className="text-[#FCA311]" />
          Action Required
        </h2>
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-gradient-to-r from-[#FCA311] to-[#e89510] rounded-2xl p-5 shadow-xl mb-3"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                <Users size={20} className="text-white" />
              </div>
              <div>
                <h4 className="font-['Poppins'] font-semibold text-white text-base">
                  Follow Up on Payments
                </h4>
                <p className="font-['Inter'] text-xs text-white/70">3 customers</p>
              </div>
            </div>
            <ArrowRight size={20} className="text-white" />
          </div>
          <p className="font-['Inter'] text-sm text-white/90 mb-3">
            Ramesh, Suresh, and Mukesh have pending payments totaling ₹8,500
          </p>
          <div className="flex items-center gap-2 text-white/90">
            <Clock size={14} />
            <span className="font-['Inter'] text-xs font-medium">Due in 2 days</span>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-gradient-to-r from-[#14213D] to-[#1a2a4d] rounded-2xl p-5 shadow-xl mb-4"
        >
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#FCA311]/20 flex items-center justify-center">
                <PackageX size={20} className="text-[#FCA311]" />
              </div>
              <div>
                <h4 className="font-['Poppins'] font-semibold text-white text-base">
                  Restock Alert
                </h4>
                <p className="font-['Inter'] text-xs text-white/60">3 items low</p>
              </div>
            </div>
            <ArrowRight size={20} className="text-white" />
          </div>
          <p className="font-['Inter'] text-sm text-white/80 mb-3">
            Rice, Sugar, and Cooking Oil running low. Order within 24 hours.
          </p>
          <div className="flex items-center gap-2 text-white/70">
            <Clock size={14} />
            <span className="font-['Inter'] text-xs font-medium">Critical stock level</span>
          </div>
        </motion.div>

        <div className="bg-gradient-to-br from-[#14213D]/5 to-transparent rounded-2xl p-4 border border-[#14213D]/10">
          <div className="flex gap-2">
            <Sparkles size={16} className="text-[#FCA311] flex-shrink-0 mt-0.5" />
            <p className="font-['Inter'] text-sm text-[#14213D]/80 leading-relaxed">
              Timely payment collection will improve your working capital by 15%. Restocking essential items prevents potential sales loss during peak hours when demand is highest.
            </p>
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-[#FCA311]/10 to-transparent rounded-3xl p-5 border border-[#FCA311]/20">
        <div className="flex items-start gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-[#FCA311]/20 flex items-center justify-center flex-shrink-0">
            <Sparkles size={20} className="text-[#FCA311]" />
          </div>
          <div>
            <h3 className="font-['Poppins'] font-semibold text-[#14213D] text-base mb-2">
              AI Recommendation
            </h3>
            <p className="font-['Inter'] text-sm text-[#14213D]/80 leading-relaxed">
              Analysis shows Thursday and Saturday see 25% higher customer footfall. Consider introducing special promotions or combo offers on these days to maximize revenue potential. Your inventory turnover is healthy, suggesting good demand-supply balance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
