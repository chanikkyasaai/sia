import { Mic } from 'lucide-react';
import { motion } from 'framer-motion';

interface MicButtonProps {
  state?: 'idle' | 'listening' | 'disabled';
  onClick: () => void;
}

export default function MicButton({ state = 'idle', onClick }: MicButtonProps) {
  const isListening = state === 'listening';

  return (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-10">
      <motion.button
        animate={
          isListening
            ? { scale: [1, 1.05, 1], boxShadow: ['0 8px 20px rgba(252, 163, 17, 0.3)', '0 12px 30px rgba(252, 163, 17, 0.5)', '0 8px 20px rgba(252, 163, 17, 0.3)'] }
            : { scale: [1, 1.02, 1] }
        }
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={onClick}
        disabled={state === 'disabled'}
        className="w-24 h-24 rounded-full bg-[#FCA311] flex items-center justify-center shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Mic size={40} className="text-[#14213D]" strokeWidth={2.5} />
      </motion.button>

      <div className="mt-4 text-center">
        <p className="font-['Poppins'] font-semibold text-[#14213D] text-sm mb-1">
          {isListening ? 'Listening...' : 'Speak to SIA'}
        </p>
        <p className="font-['Inter'] text-xs text-gray-600 max-w-[200px]">
          Say: "Aaj 500 ka samaan becha"
        </p>
      </div>
    </div>
  );
}
