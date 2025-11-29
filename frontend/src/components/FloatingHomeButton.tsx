import { Home } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

export default function FloatingHomeButton() {
  const navigate = useNavigate();
  const location = useLocation();
  const isActive = location.pathname === '/';

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => navigate('/')}
        className={`px-8 py-3 rounded-full shadow-lg flex items-center gap-2 font-['Poppins'] font-semibold transition-all ${
          isActive
            ? 'bg-[#14213D]/70 text-white border-2 border-[#FCA311]'
            : 'bg-[#14213D] text-white hover:shadow-xl'
        }`}
      >
        <Home size={20} />
        <span>Home</span>
      </motion.button>
    </div>
  );
}
