import { Home, BarChart3, Database, MessageSquare, User } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { icon: BarChart3, label: 'Analytics', path: '/analytics' },
  { icon: Database, label: 'Data', path: '/data' },
  { icon: Home, label: 'Home', path: '/' },
  { icon: MessageSquare, label: 'Chat', path: '/history' },
  { icon: User, label: 'Profile', path: '/profile' },
];

export default function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 pb-safe">
      <div className="max-w-[480px] mx-auto px-4 pb-5">
        <motion.div
          initial={{ y: 100, opacity: 0, scale: 0.9 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          transition={{
            type: 'spring',
            stiffness: 200,
            damping: 25,
            delay: 0.2
          }}
          className="relative bg-[#14213D]/95 backdrop-blur-xl rounded-[24px] px-2 py-3 shadow-xl border border-white/10"
        >
          {/* Ambient glow - more subtle */}
          <div className="absolute -inset-0.5 bg-gradient-to-r from-[#FCA311]/10 via-transparent to-[#FCA311]/10 rounded-[24px] blur-lg -z-10" />

          <div className="flex items-center justify-around relative">
            {navItems.map((item, index) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              const isCenter = index === 2;

              return (
                <motion.button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  whileTap={{ scale: 0.9 }}
                  whileHover={{ scale: 1.02 }}
                  className={`relative flex flex-col items-center gap-1 rounded-[18px] transition-all ${
                    isCenter ? 'px-4 py-2.5' : 'px-3 py-2'
                  }`}
                >
                  {/* Glow effect for active item - dispersed orange shadow */}
                  {isActive && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.5 }}
                      animate={{ opacity: 0.4, scale: 1.2 }}
                      className="absolute inset-0 bg-[#FCA311] rounded-[20px] blur-2xl -z-10"
                    />
                  )}

                  {/* Icon with premium animation */}
                  <motion.div
                    animate={isActive ? {
                      y: [0, -1, 0],
                    } : {}}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      ease: 'easeInOut'
                    }}
                    className="relative z-10"
                  >
                    <Icon
                      size={isCenter ? 24 : 20}
                      className={`transition-all duration-300 ${
                        isActive ? 'text-white' : 'text-white/90'
                      }`}
                      strokeWidth={isActive ? 2.5 : 2}
                    />
                  </motion.div>

                  {/* Label */}
                  <motion.span
                    animate={isActive ? {
                      opacity: 1,
                      y: 0
                    } : {
                      opacity: 0.8,
                      y: 0
                    }}
                    className={`relative z-10 text-caption text-[9px] font-semibold tracking-wide transition-colors ${
                      isActive ? 'text-white' : 'text-white/80'
                    }`}
                  >
                    {item.label}
                  </motion.span>

                  {/* Dot indicator below */}
                  <AnimatePresence>
                    {isActive && (
                      <motion.div
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                        className="absolute -bottom-1.5 w-1.5 h-1.5 bg-[#FCA311] rounded-full shadow-[0_0_8px_rgba(252,163,17,0.8)]"
                      />
                    )}
                  </AnimatePresence>
                </motion.button>
              );
            })}
          </div>


        </motion.div>
      </div>
    </div>
  );
}
