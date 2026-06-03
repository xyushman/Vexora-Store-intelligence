"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, Bot, AlertCircle, TrendingUp } from "lucide-react";

export default function AIAssistant({ anomalies }: { anomalies?: any[] }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState("");
  const [isTyping, setIsTyping] = useState(true);

  // Map API anomalies to insights
  const insights = anomalies && anomalies.length > 0 
    ? anomalies.map(anom => ({
        icon: anom.severity === 'CRITICAL' ? AlertCircle : (anom.severity === 'WARN' ? TrendingUp : Sparkles),
        text: anom.suggested_action || anom.detail?.insight || `Anomaly detected: ${anom.type}`,
        type: anom.severity === 'CRITICAL' ? 'alert' : 'insight'
      }))
    : [
        { icon: Bot, text: "System optimal. Monitoring store zones.", type: "system" }
      ];

  // Prevent index out of bounds when anomalies change
  const activeIndex = currentIndex < insights.length ? currentIndex : 0;

  useEffect(() => {
    // Typing effect
    const fullText = insights[activeIndex].text;
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

    return () => clearInterval(typingInterval);
  }, [activeIndex, insights.length]); // Re-run typing when text changes

  useEffect(() => {
    if (insights.length <= 1) return;
    const rotateInterval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % insights.length);
    }, 10000);
    return () => clearInterval(rotateInterval);
  }, [insights.length]);

  const CurrentIcon = insights[activeIndex].icon;

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
            key={activeIndex}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="flex items-start gap-3"
          >
            <div className={`mt-1 p-1.5 rounded-lg border ${
              insights[activeIndex].type === 'alert' ? 'bg-red-500/10 border-red-500/30 text-red-400' :
              insights[activeIndex].type === 'insight' ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' :
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
        <span>Model: Gemini 2.5 Flash</span>
        <span className="flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-green-500"></div> Connected</span>
      </div>
    </div>
  );
}
