"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Bot, AlertCircle, TrendingUp } from "lucide-react";

const INSIGHTS = [
  { icon: TrendingUp, text: "Customer dwell time in the Mens section is currently 25% higher than the weekly average. Consider highlighting premium accessories.", type: "insight" },
  { icon: AlertCircle, text: "Queue depth at Billing is increasing. Suggest deploying Staff ID 2 to open Register 3.", type: "alert" },
  { icon: Sparkles, text: "Conversion rate for the last hour is showing strong momentum. Peak traffic predicted in 15 minutes.", type: "insight" },
  { icon: Bot, text: "Monitoring 4 zones. Anomaly detection active. System health is optimal.", type: "system" }
];

export default function AIAssistant() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState("");
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    // Typing effect
    const fullText = INSIGHTS[currentIndex].text;
    let i = 0;
    setIsTyping(true);
    setDisplayedText("");
    
    const typingInterval = setInterval(() => {
      setDisplayedText(fullText.substring(0, i));
      i++;
      if (i > fullText.length) {
        clearInterval(typingInterval);
        setIsTyping(false);
      }
    }, 40);

    // Change insight every 10 seconds
    const rotateInterval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % INSIGHTS.length);
    }, 10000);

    return () => {
      clearInterval(typingInterval);
      clearInterval(rotateInterval);
    };
  }, [currentIndex]);

  const CurrentIcon = INSIGHTS[currentIndex].icon;

  return (
    <div className="glass-panel p-5 relative overflow-hidden h-full flex flex-col group">
      {/* Animated glowing border */}
      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-blue-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
      <div className="absolute -inset-[100%] animate-[spin_4s_linear_infinite] opacity-20 pointer-events-none" 
           style={{ background: 'conic-gradient(from 90deg at 50% 50%, transparent 0%, var(--accent-blue) 50%, transparent 100%)' }} />
      
      <div className="relative z-10 flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/50 relative">
            <div className="absolute inset-0 bg-blue-500/20 rounded-full animate-ping" />
            <Bot size={16} className="text-blue-400" />
          </div>
          <h3 className="font-bold text-sm tracking-widest text-blue-400 uppercase">Vexora AI Manager</h3>
        </div>
        <div className="flex gap-1">
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse delay-75" />
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse delay-150" />
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse delay-300" />
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center relative z-10">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="flex items-start gap-3"
          >
            <div className={`mt-1 p-1.5 rounded-lg border ${
              INSIGHTS[currentIndex].type === 'alert' ? 'bg-red-500/10 border-red-500/30 text-red-400' :
              INSIGHTS[currentIndex].type === 'insight' ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' :
              'bg-blue-500/10 border-blue-500/30 text-blue-400'
            }`}>
              <CurrentIcon size={18} />
            </div>
            <div className="flex-1 min-h-[80px]">
              <p className="text-sm md:text-base leading-relaxed text-black/80 dark:text-white/80 font-medium">
                {displayedText}
                {isTyping && <span className="inline-block w-1.5 h-4 ml-1 bg-blue-500 animate-pulse" />}
              </p>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
      
      <div className="relative z-10 mt-auto pt-4 border-t border-black/5 dark:border-white/10 flex items-center justify-between text-xs text-black/40 dark:text-white/40">
        <span>Model: Vexora-Vision-7B</span>
        <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-500"></div> Connected</span>
      </div>
    </div>
  );
}
