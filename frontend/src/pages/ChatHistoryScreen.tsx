import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Bot, Sparkles } from 'lucide-react';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: string;
}

interface DateSection {
  date: string;
  messages: Message[];
}

export default function ChatHistoryScreen() {
  const chatContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, []);

  const chatSections: DateSection[] = [
    {
      date: 'Yesterday',
      messages: [
        { id: 9, text: 'Stock mein kya kam hai?', sender: 'user', timestamp: '6:45 PM' },
        {
          id: 10,
          text: 'Rice, Sugar, and Cooking Oil are running low. You should restock within 24 hours.',
          sender: 'ai',
          timestamp: '6:45 PM',
        },
        {
          id: 11,
          text: 'Is hafte ka total expense batao',
          sender: 'user',
          timestamp: '8:10 PM',
        },
        {
          id: 12,
          text: 'This week\'s total expenses: ₹12,850. Main categories: Stock purchases (₹8,200), Utilities (₹2,100), Miscellaneous (₹2,550).',
          sender: 'ai',
          timestamp: '8:10 PM',
        },
      ],
    },
    {
      date: 'Today',
      messages: [
        { id: 1, text: 'Aaj 500 ka samaan becha', sender: 'user', timestamp: '9:30 AM' },
        {
          id: 2,
          text: 'Great! ₹500 ki sale recorded. Your today\'s total revenue is now ₹4,750.',
          sender: 'ai',
          timestamp: '9:30 AM',
        },
        { id: 3, text: 'Kitna profit hua aaj?', sender: 'user', timestamp: '2:15 PM' },
        {
          id: 4,
          text: 'Today\'s profit is ₹4,250. You\'re doing 18% better than yesterday!',
          sender: 'ai',
          timestamp: '2:15 PM',
        },
        {
          id: 5,
          text: 'Ramesh ka pending payment check karo',
          sender: 'user',
          timestamp: '4:20 PM',
        },
        {
          id: 6,
          text: 'Ramesh has a pending payment of ₹3,500, due in 2 days. Would you like me to send him a reminder?',
          sender: 'ai',
          timestamp: '4:20 PM',
        },
        { id: 7, text: 'Haan bhej do reminder', sender: 'user', timestamp: '4:22 PM' },
        {
          id: 8,
          text: 'Reminder sent to Ramesh! I\'ll keep you updated on his response.',
          sender: 'ai',
          timestamp: '4:22 PM',
        },
      ],
    },
  ];

  return (
    <div className="h-screen flex flex-col bg-gradient-to-b from-[#0a0118]/5 via-white to-gray-50">
      {/* Premium Header */}
      <div className="bg-gradient-to-br from-[#14213D] via-[#1a2a4d] to-[#14213D] px-4 pt-12 pb-6 shadow-2xl relative overflow-hidden">
        {/* Decorative blur */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#FCA311]/10 rounded-full blur-[100px]" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#FCA311] to-orange-600 flex items-center justify-center shadow-xl">
              <Bot size={24} className="text-white" strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-heading text-white text-xl">SIA Intelligence</h1>
              <p className="text-caption text-white/60 text-xs">Voice Chat History</p>
            </div>
          </div>
        </div>
      </div>

      {/* Chat messages */}
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto px-5 py-6 space-y-8 pb-32">
        {chatSections.map((section, sectionIndex) => (
          <motion.div
            key={sectionIndex}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: sectionIndex * 0.1 }}
          >
            {/* Date divider */}
            <div className="flex items-center justify-center mb-6">
              <div className="bg-[#14213D]/8 backdrop-blur-sm px-5 py-2 rounded-full shadow-sm">
                <p className="text-caption text-[#14213D]/70 text-xs font-semibold tracking-wide">
                  {section.date}
                </p>
              </div>
            </div>

            {/* Messages */}
            <div className="space-y-4">
              {section.messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 15, x: message.sender === 'user' ? 30 : -30 }}
                  animate={{ opacity: 1, y: 0, x: 0 }}
                  transition={{ delay: index * 0.05, duration: 0.4, type: 'spring', stiffness: 120 }}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[78%] ${
                      message.sender === 'user'
                        ? 'bg-gradient-to-br from-[#FCA311] to-[#e89510] text-white rounded-[22px] rounded-tr-md shadow-lg'
                        : 'bg-white text-[#14213D] rounded-[22px] rounded-tl-md border border-[#14213D]/8 shadow-md'
                    } px-5 py-3.5 relative`}
                  >
                    {message.sender === 'ai' && (
                      <div className="flex items-center gap-2 mb-2">
                        <div className="w-5 h-5 rounded-full bg-gradient-to-br from-[#14213D] to-[#1a2a4d] flex items-center justify-center shadow-sm">
                          <Sparkles size={11} className="text-[#FCA311]" strokeWidth={3} />
                        </div>
                        <span className="text-caption text-[#14213D]/60 text-[10px] font-semibold tracking-wide">
                          SIA
                        </span>
                      </div>
                    )}
                    <p
                      className={`text-body text-[14px] leading-relaxed ${
                        message.sender === 'user' ? 'text-white' : 'text-[#14213D]'
                      }`}
                    >
                      {message.text}
                    </p>
                    <p
                      className={`text-caption text-[11px] mt-2 ${
                        message.sender === 'user' ? 'text-white/70' : 'text-[#14213D]/50'
                      } text-right tracking-wide`}
                    >
                      {message.timestamp}
                    </p>

                    {/* Premium shadow accent */}
                    {message.sender === 'user' && (
                      <div className="absolute -bottom-1 -right-1 w-full h-full bg-[#FCA311]/20 rounded-[22px] rounded-tr-md blur-lg -z-10" />
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        ))}

        {/* Premium CTA */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 }}
          className="mt-8 bg-gradient-to-br from-[#14213D]/5 to-transparent rounded-3xl p-6 border border-[#14213D]/10"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#FCA311] to-orange-600 flex items-center justify-center shadow-lg flex-shrink-0">
              <Bot size={24} className="text-white" strokeWidth={2.5} />
            </div>
            <div>
              <h3 className="text-heading text-[#14213D] text-base mb-2">
                Start a new conversation
              </h3>
              <p className="text-body text-[#14213D]/70 text-sm leading-relaxed">
                Go to the Home screen and tap to speak with SIA about your business.
              </p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Empty state */}
      {chatSections.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center justify-center h-full text-center px-8"
        >
          <div className="w-32 h-32 rounded-3xl bg-gradient-to-br from-[#14213D] to-[#1a2a4d] flex items-center justify-center mb-8 shadow-2xl">
            <Bot size={56} className="text-white" strokeWidth={2} />
          </div>
          <h3 className="text-heading text-[#14213D] text-2xl mb-3">
            No conversations yet
          </h3>
          <p className="text-body text-[#14213D]/70 leading-relaxed max-w-sm">
            Start by speaking to SIA on the Home screen. Your voice interactions will appear here.
          </p>
        </motion.div>
      )}
    </div>
  );
}
