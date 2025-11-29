import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import { VoiceWebSocketClient } from '../services/voiceWebSocket';

interface AIVoiceInterfaceProps {
  isListening: boolean;
  onTranscription?: (text: string) => void;
  onClearCaption?: () => void;
}

export default function AIVoiceInterface({ isListening }: AIVoiceInterfaceProps) {
  const [status, setStatus] = useState<'idle' | 'connecting' | 'listening' | 'processing' | 'speaking' | 'error'>('idle');
  const [transcription, setTranscription] = useState('');
  const [fullTranscript, setFullTranscript] = useState('');
  const [agentResponse, setAgentResponse] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const voiceClientRef = useRef<VoiceWebSocketClient | null>(null);
  const isActiveRef = useRef(false);

  useEffect(() => {
    // Initialize WebSocket client on mount
    const initializeVoiceClient = async () => {
      if (voiceClientRef.current) return;

      setStatus('connecting');

      const client = new VoiceWebSocketClient({
        onSessionInitialized: (sessionId) => {
          console.log('Session initialized:', sessionId);
          setIsConnected(true);
          setStatus('idle');
          setErrorMessage('');
        },
        onTranscription: (text, isFinal) => {
          setTranscription(text);
          if (onTranscription) {
            onTranscription(text);
          }
          if (isFinal) {
            console.log('Final transcription:', text);
          }
        },
        onProcessing: (message) => {
          setStatus('processing');
          setAgentResponse(message);
        },
        onAgentSpeaking: (text) => {
          setStatus('speaking');
          setAgentResponse(text);
          setTranscription('');
          if (onClearCaption) {
            onClearCaption();
          }
        },
        onAgentFinished: (sessionComplete) => {
          setStatus('idle');
          setTimeout(() => {
            setAgentResponse('');
          }, 3000);
        },
        onInterrupted: (spokenText, hasPendingWork) => {
          console.log('Agent interrupted:', { spokenText, hasPendingWork });
        },
        onError: (error) => {
          setStatus('error');
          setErrorMessage(error);
          console.error('Voice error:', error);
        },
        onDisconnected: () => {
          setIsConnected(false);
          setStatus('idle');
        },
        onTimeout: () => {
          setStatus('error');
          setErrorMessage('Session expired due to inactivity');
        }
      });

      voiceClientRef.current = client;

      try {
        await client.connect(2, 1);
      } catch (error) {
        console.error('Failed to connect:', error);
        setStatus('error');
        setErrorMessage('Failed to connect to voice service');
      }
    };

    initializeVoiceClient();

    // Cleanup on unmount
    return () => {
      if (voiceClientRef.current) {
        voiceClientRef.current.disconnect();
        voiceClientRef.current = null;
      }
    };
  }, []);

  // Handle listening state changes
  useEffect(() => {
    const client = voiceClientRef.current;
    if (!client || !isConnected) return;

    if (isListening && !isActiveRef.current) {
      // Start recording
      isActiveRef.current = true;
      setStatus('listening');
      setTranscription('');
      setFullTranscript('');
      setErrorMessage('');
      
      client.startRecording().catch((error) => {
        console.error('Failed to start recording:', error);
        setStatus('error');
        
        // Provide helpful error message based on the error
        const errorMsg = error.message || String(error);
        if (errorMsg.includes('localhost') || errorMsg.includes('HTTPS')) {
          setErrorMessage('Microphone requires HTTPS or localhost access. Please use http://localhost:5173');
        } else if (errorMsg.includes('Permission denied') || errorMsg.includes('NotAllowedError')) {
          setErrorMessage('Microphone access denied. Please allow microphone permissions.');
        } else {
          setErrorMessage('Failed to access microphone. Please check permissions.');
        }
        
        isActiveRef.current = false;
      });
    } else if (!isListening && isActiveRef.current) {
      // Stop recording
      client.stopRecording();
      isActiveRef.current = false;
      
      if (status === 'listening') {
        setStatus('idle');
      }
    }
  }, [isListening, isConnected, status]);

  const getStatusMessage = () => {
    if (!isConnected && status === 'connecting') return 'Connecting...';
    if (!isConnected) return 'Not connected';
    if (status === 'error') return errorMessage;
    if (status === 'connecting') return 'Connecting to Sia...';
    if (status === 'listening') return 'Listening...';
    if (status === 'processing') return agentResponse || 'Sia is thinking...';
    if (status === 'speaking') return 'Sia is speaking...';
    return 'Tap to speak';
  };

  const getStatusColor = () => {
    if (status === 'error') return 'from-red-500 to-red-600';
    if (status === 'processing') return 'from-blue-500 to-blue-600';
    if (status === 'speaking') return 'from-purple-500 to-purple-600';
    if (status === 'listening') return 'from-[#FCA311] to-orange-600';
    return 'from-[#FCA311] to-orange-600';
  };

  const isSpeaking = status === 'listening' || status === 'processing' || status === 'speaking';

  return (
    <div className="relative w-full h-screen flex flex-col overflow-hidden bg-gradient-to-b from-[#0a0118] via-[#14213D] to-[#0a0118] cursor-pointer">
      {/* Liquid flowing gradient blobs - speed increases when listening */}
      <motion.div
        animate={{
          x: [0, 100, -50, 0],
          y: [0, -80, 50, 0],
          scale: [1, 1.2, 0.9, 1],
        }}
        transition={{
          duration: isSpeaking ? 3 : 12,
          repeat: Infinity,
          ease: 'easeInOut',
        }}
        className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-600/20 blur-[120px] pointer-events-none"
      />
      <motion.div
        animate={{
          x: [0, -80, 100, 0],
          y: [0, 100, -60, 0],
          scale: [1, 0.8, 1.3, 1],
        }}
        transition={{
          duration: isSpeaking ? 2 : 10,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: 2,
        }}
        className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-gradient-to-br from-[#FCA311]/20 to-orange-600/20 blur-[120px] pointer-events-none"
      />
      <motion.div
        animate={{
          x: [0, -60, 80, 0],
          y: [0, 60, -80, 0],
          scale: [1, 1.1, 0.85, 1],
        }}
        transition={{
          duration: isSpeaking ? 2.5 : 14,
          repeat: Infinity,
          ease: 'easeInOut',
          delay: 1,
        }}
        className="absolute top-1/2 right-1/3 w-80 h-80 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-600/20 blur-[120px] pointer-events-none"
      />

      {/* Extra intense listening blob */}
      <AnimatePresence>
        {isSpeaking && (
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.5 }}
            className="absolute inset-0 pointer-events-none"
          >
            <motion.div
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-gradient-to-br from-[#FCA311]/30 to-orange-600/30 blur-[100px]"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Top badge centered with glare effect */}
      <div className="relative z-20 pt-16 flex justify-center pointer-events-none">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: -30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{
            type: 'spring',
            stiffness: 200,
            damping: 20,
            delay: 0.2
          }}
          className="relative inline-block bg-white/5 backdrop-blur-2xl px-6 py-3 rounded-full border border-white/10 overflow-hidden shadow-2xl"
        >
          <motion.div
            animate={{
              x: ['-100%', '200%'],
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: 'easeInOut',
              repeatDelay: 2,
            }}
            className="absolute inset-0 w-1/2 bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12"
          />
          <p className="text-display text-white text-sm font-bold tracking-[0.15em] relative z-10">
            SIA INTELLIGENCE
          </p>
        </motion.div>
      </div>

      {/* Main content - Left aligned, moved higher */}
      <div className="relative z-10 flex-1 flex flex-col justify-center px-6 pb-48 pointer-events-none">
        <motion.div
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{
            type: 'spring',
            stiffness: 100,
            damping: 20,
            delay: 0.4
          }}
          className="max-w-sm w-full"
        >
          <motion.h1
            className="text-display text-white text-[56px] leading-[1.1] mb-5"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8, type: 'spring', stiffness: 100 }}
          >
            Hi Ravi,
          </motion.h1>

          <motion.div
            className="space-y-3 mb-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.6 }}
          >
            {agentResponse && status === 'speaking' ? (
              <p className="text-body text-white/95 text-xl leading-relaxed font-medium">
                {agentResponse}
              </p>
            ) : (
              <>
                <p className="text-body text-white/95 text-xl leading-relaxed font-medium">
                  SIA is watching your business today.
                </p>
                <p className="text-body text-white/75 text-base leading-relaxed">
                  Your personal financial coach, always on.
                </p>
              </>
            )}
          </motion.div>

          {/* Live captions - shows what user is saying */}
          <AnimatePresence>
            {(transcription || fullTranscript) && status === 'listening' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-6 bg-white/10 backdrop-blur-xl px-5 py-3 rounded-2xl border border-white/20"
              >
                <p className="text-white/60 text-xs font-semibold tracking-wide mb-1">
                  YOU'RE SAYING
                </p>
                <p className="text-white text-base leading-relaxed">
                  {fullTranscript} <span className="text-[#FCA311]">{transcription}</span>
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Status indicator - shows current state */}
          <AnimatePresence mode="wait">
            {!isSpeaking ? (
              <motion.div
                key="idle"
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                className={`inline-flex items-center gap-3 bg-[#FCA311]/15 backdrop-blur-xl px-6 py-3.5 rounded-full border ${status === 'error' ? 'border-red-500/50' : 'border-[#FCA311]/30'} shadow-lg`}
              >
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                  className={`w-2.5 h-2.5 rounded-full ${status === 'error' ? 'bg-red-500' : 'bg-[#FCA311]'}`}
                />
                <p className={`text-caption text-sm font-bold tracking-wide ${status === 'error' ? 'text-red-400' : 'text-[#FCA311]'}`}>
                  {getStatusMessage()}
                </p>
              </motion.div>
            ) : (
              <motion.div
                key="active"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                className={`inline-flex items-center gap-3 bg-gradient-to-br ${getStatusColor()} backdrop-blur-xl px-6 py-3.5 rounded-full border border-white/20 shadow-2xl`}
              >
                {/* Animated sound waves */}
                <div className="flex items-center gap-1">
                  {[0, 1, 2, 3].map((i) => (
                    <motion.div
                      key={i}
                      animate={{
                        height: ['8px', '20px', '8px'],
                      }}
                      transition={{
                        duration: 0.8,
                        repeat: Infinity,
                        ease: 'easeInOut',
                        delay: i * 0.15,
                      }}
                      className="w-1 bg-white rounded-full"
                    />
                  ))}
                </div>

                {/* Status text */}
                <p className="text-caption text-white text-sm font-bold tracking-wide">
                  {getStatusMessage()}
                </p>

                {/* Pulse dot */}
                <motion.div
                  animate={{
                    scale: [1, 1.3, 1],
                    opacity: [1, 0.5, 1],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  }}
                  className="w-2 h-2 bg-white rounded-full"
                />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-56 bg-gradient-to-t from-[#0a0118] via-[#0a0118]/70 to-transparent pointer-events-none" />
    </div>
  );
}
