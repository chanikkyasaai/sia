import { motion } from 'framer-motion';
import { Store, User, Phone, Globe, LogOut, Bell, Zap, ChevronRight, Crown, Mic, Calendar, Sparkles } from 'lucide-react';
import { useState } from 'react';

export default function ProfileSettingsScreen() {
  const [handsFreeMode, setHandsFreeMode] = useState(true);
  const [notifications, setNotifications] = useState(true);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0a0118]/5 to-white p-6 pt-8 pb-32">
      <div className="mb-8">
        <h1 className="text-display text-[#14213D] text-2xl mb-1">
          Profile & Settings
        </h1>
        <p className="text-body text-[#14213D]/60 text-sm">
          Manage your account and preferences
        </p>
      </div>

      {/* Profile Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-br from-[#14213D] via-[#1a2a4d] to-[#14213D] rounded-3xl p-6 mb-6 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-48 h-48 bg-[#FCA311]/15 rounded-full -translate-y-1/2 translate-x-1/2 blur-[100px]" />

        <div className="relative z-10 flex items-center gap-4">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[#FCA311] to-orange-600 flex items-center justify-center text-white text-display text-2xl shadow-xl">
            RK
          </div>
          <div className="flex-1">
            <h2 className="text-heading text-white text-xl mb-1">Ravi Kumar</h2>
            <p className="text-body text-white/70 text-sm mb-1">Ravi General Store</p>
            <p className="text-caption text-white/60 text-xs">+91 98765 43210</p>
          </div>
        </div>
      </motion.div>

      {/* Subscription Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gradient-to-br from-[#FCA311] via-[#FCA311] to-orange-600 rounded-3xl p-6 mb-6 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute -top-12 -right-12 w-32 h-32 border-4 border-white/10 rounded-full" />
        <div className="absolute -bottom-8 -left-8 w-24 h-24 border-4 border-white/10 rounded-full" />

        <div className="relative z-10">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <Crown size={24} className="text-white" strokeWidth={2.5} />
              </div>
              <div>
                <h3 className="text-heading text-white text-lg">Premium Plan</h3>
                <p className="text-caption text-white/80 text-xs">Active</p>
              </div>
            </div>
            <div className="w-3 h-3 rounded-full bg-[#22C55E] animate-pulse shadow-lg" />
          </div>

          <div className="bg-white/15 backdrop-blur-sm rounded-2xl p-4 mb-4 border border-white/10">
            <div className="flex items-center gap-3 mb-3">
              <Calendar size={18} className="text-white/90" />
              <p className="text-caption text-white/90 text-xs font-medium">Next Renewal</p>
            </div>
            <p className="text-display text-white text-2xl">Dec 28, 2025</p>
            <p className="text-caption text-white/70 text-xs mt-1">30 days remaining</p>
          </div>

          <motion.button
            whileTap={{ scale: 0.98 }}
            className="w-full bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded-2xl py-3 text-caption font-semibold flex items-center justify-center gap-2 transition-all border border-white/10"
          >
            <Sparkles size={16} />
            Manage Subscription
          </motion.button>
        </div>
      </motion.div>

      {/* Voice Credits Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-gradient-to-br from-[#14213D] to-[#1a2a4d] rounded-3xl p-6 mb-6 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-40 h-40 bg-[#FCA311]/20 rounded-full -translate-y-1/2 translate-x-1/2 blur-[80px]" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-2xl bg-[#FCA311]/20 flex items-center justify-center">
              <Mic size={24} className="text-[#FCA311]" strokeWidth={2.5} />
            </div>
            <div>
              <h3 className="text-heading text-white text-lg">Voice Credits</h3>
              <p className="text-caption text-white/60 text-xs">For AI conversations</p>
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-5 mb-4 border border-white/10">
            <p className="text-caption text-white/70 text-xs mb-2">Available Credits</p>
            <div className="flex items-end gap-2 mb-3">
              <p className="text-display text-white text-4xl">2,450</p>
              <p className="text-body text-white/60 text-sm mb-2">minutes</p>
            </div>

            {/* Progress bar */}
            <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: '82%' }}
                transition={{ delay: 0.5, duration: 1, ease: 'easeOut' }}
                className="h-full bg-gradient-to-r from-[#FCA311] to-orange-600 rounded-full"
              />
            </div>
            <p className="text-caption text-white/60 text-xs mt-2">82% remaining</p>
          </div>

          <motion.button
            whileTap={{ scale: 0.98 }}
            className="w-full bg-[#FCA311] hover:bg-[#FCA311]/90 text-white rounded-2xl py-3 text-caption font-semibold flex items-center justify-center gap-2 transition-all shadow-lg"
          >
            <Sparkles size={16} />
            Buy More Credits
          </motion.button>
        </div>
      </motion.div>

      {/* Business Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white rounded-3xl p-6 mb-6 shadow-lg border border-[#14213D]/10"
      >
        <h3 className="text-heading text-[#14213D] text-base mb-4">
          Business Information
        </h3>

        <div className="space-y-3">
          <motion.div
            whileTap={{ scale: 0.98 }}
            className="flex items-center justify-between p-4 rounded-2xl bg-[#14213D]/5 hover:bg-[#14213D]/10 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#14213D]/10 flex items-center justify-center">
                <Store size={20} className="text-[#14213D]" />
              </div>
              <div>
                <p className="text-caption text-[#14213D]/60 text-xs">Business Name</p>
                <p className="text-body text-[#14213D] font-semibold text-sm">Ravi General Store</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-[#14213D]/40" />
          </motion.div>

          <motion.div
            whileTap={{ scale: 0.98 }}
            className="flex items-center justify-between p-4 rounded-2xl bg-[#14213D]/5 hover:bg-[#14213D]/10 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#14213D]/10 flex items-center justify-center">
                <User size={20} className="text-[#14213D]" />
              </div>
              <div>
                <p className="text-caption text-[#14213D]/60 text-xs">Owner Name</p>
                <p className="text-body text-[#14213D] font-semibold text-sm">Ravi Kumar</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-[#14213D]/40" />
          </motion.div>

          <motion.div
            whileTap={{ scale: 0.98 }}
            className="flex items-center justify-between p-4 rounded-2xl bg-[#14213D]/5 hover:bg-[#14213D]/10 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#14213D]/10 flex items-center justify-center">
                <Phone size={20} className="text-[#14213D]" />
              </div>
              <div>
                <p className="text-caption text-[#14213D]/60 text-xs">Phone Number</p>
                <p className="text-body text-[#14213D] font-semibold text-sm">+91 98765 43210</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-[#14213D]/40" />
          </motion.div>
        </div>
      </motion.div>

      {/* Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-white rounded-3xl p-6 mb-6 shadow-lg border border-[#14213D]/10"
      >
        <h3 className="text-heading text-[#14213D] text-base mb-4">
          Preferences
        </h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 rounded-2xl bg-[#14213D]/5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#FCA311]/10 flex items-center justify-center">
                <Zap size={20} className="text-[#FCA311]" />
              </div>
              <div>
                <p className="text-body text-[#14213D] font-semibold text-sm">Hands-Free Mode</p>
                <p className="text-caption text-[#14213D]/60 text-xs">Auto-listen for commands</p>
              </div>
            </div>
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setHandsFreeMode(!handsFreeMode)}
              className={`relative w-14 h-8 rounded-full transition-colors ${
                handsFreeMode ? 'bg-[#22C55E]' : 'bg-[#14213D]/20'
              }`}
            >
              <motion.div
                animate={{ x: handsFreeMode ? 24 : 2 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
              />
            </motion.button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-2xl bg-[#14213D]/5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#14213D]/10 flex items-center justify-center">
                <Bell size={20} className="text-[#14213D]" />
              </div>
              <div>
                <p className="text-body text-[#14213D] font-semibold text-sm">Notifications</p>
                <p className="text-caption text-[#14213D]/60 text-xs">Get alerts and reminders</p>
              </div>
            </div>
            <motion.button
              whileTap={{ scale: 0.9 }}
              onClick={() => setNotifications(!notifications)}
              className={`relative w-14 h-8 rounded-full transition-colors ${
                notifications ? 'bg-[#22C55E]' : 'bg-[#14213D]/20'
              }`}
            >
              <motion.div
                animate={{ x: notifications ? 24 : 2 }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                className="absolute top-1 w-6 h-6 bg-white rounded-full shadow-md"
              />
            </motion.button>
          </div>

          <motion.div
            whileTap={{ scale: 0.98 }}
            className="flex items-center justify-between p-4 rounded-2xl bg-[#14213D]/5 hover:bg-[#14213D]/10 transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#14213D]/10 flex items-center justify-center">
                <Globe size={20} className="text-[#14213D]" />
              </div>
              <div>
                <p className="text-body text-[#14213D] font-semibold text-sm">Language</p>
                <p className="text-caption text-[#14213D]/60 text-xs">Hinglish (Hindi + English)</p>
              </div>
            </div>
            <ChevronRight size={20} className="text-[#14213D]/40" />
          </motion.div>
        </div>
      </motion.div>

      {/* Logout Button */}
      <motion.button
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full bg-gradient-to-r from-[#EF4444] to-red-600 text-white rounded-3xl py-4 text-heading font-semibold flex items-center justify-center gap-3 shadow-xl hover:shadow-2xl transition-shadow"
      >
        <LogOut size={20} />
        Logout
      </motion.button>
    </div>
  );
}
