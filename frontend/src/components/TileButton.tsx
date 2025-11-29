import { LucideIcon } from 'lucide-react';
import { motion } from 'framer-motion';

interface TileButtonProps {
  icon: LucideIcon;
  label: string;
  onClick: () => void;
}

export default function TileButton({ icon: Icon, label, onClick }: TileButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.03, boxShadow: '0 10px 30px rgba(0,0,0,0.15)' }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className="bg-[#E5E5E5] rounded-2xl p-6 flex flex-col items-center justify-center gap-3 shadow-md hover:shadow-xl transition-shadow min-h-[140px]"
    >
      <Icon size={32} className="text-[#14213D]" strokeWidth={2.5} />
      <span className="font-['Poppins'] font-semibold text-[#000000] text-center text-sm">
        {label}
      </span>
    </motion.button>
  );
}
