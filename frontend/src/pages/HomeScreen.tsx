import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AIVoiceInterface from '../components/AIVoiceInterface';

export default function HomeScreen() {
  const [isListening, setIsListening] = useState(false);
  const [liveCaption, setLiveCaption] = useState('');

  return (
    <div className="relative h-screen" onClick={() => setIsListening(!isListening)}>
      <AIVoiceInterface 
        isListening={isListening} 
        onTranscription={(text) => setLiveCaption(text)}
        onClearCaption={() => setLiveCaption('')}
      />
      
      {/* Live Captions Display */}
      <AnimatePresence>
        {liveCaption && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="absolute bottom-28 left-0 right-0 px-6 pointer-events-none z-50"
          >
            <div className="bg-black/80 backdrop-blur-xl rounded-2xl px-6 py-4 border border-white/10 shadow-2xl">
              <p className="text-white/60 text-xs font-medium mb-1 tracking-wide">YOU SAID</p>
              <p className="text-white text-lg leading-relaxed">
                {liveCaption}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
