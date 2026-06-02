"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function LiveVisionFeeds() {
  const [activeCam, setActiveCam] = useState(1);
  const [boxes, setBoxes] = useState<any[]>([]);

  useEffect(() => {
    // Switch cameras every 8 seconds
    const camInterval = setInterval(() => {
      setActiveCam(prev => (prev % 3) + 1);
    }, 8000);

    // Randomize bounding boxes every 1.5 seconds to simulate AI vision
    const boxInterval = setInterval(() => {
      const numBoxes = Math.floor(Math.random() * 4) + 1; // 1 to 4 boxes
      const newBoxes = Array.from({ length: numBoxes }).map((_, i) => ({
        id: i,
        x: Math.random() * 60 + 10, // 10% to 70%
        y: Math.random() * 50 + 10,
        width: Math.random() * 15 + 10,
        height: Math.random() * 25 + 15,
        type: Math.random() > 0.8 ? 'STAFF' : 'PERSON',
        confidence: (Math.random() * 5 + 94).toFixed(1) // 94.0 to 99.0
      }));
      setBoxes(newBoxes);
    }, 1500);

    return () => {
      clearInterval(camInterval);
      clearInterval(boxInterval);
    };
  }, []);

  return (
    <div className="glass-panel p-1 relative overflow-hidden h-full flex flex-col group bg-black">
      {/* Glitch overlay */}
      <div className="absolute inset-0 pointer-events-none opacity-10 mix-blend-overlay z-20" 
           style={{ backgroundImage: 'repeating-linear-gradient(transparent, transparent 2px, black 2px, black 4px)' }} />
      
      {/* Feed Status */}
      <div className="absolute top-4 left-4 z-30 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
        <span className="text-[10px] font-bold text-white tracking-widest bg-black/50 px-2 py-0.5 rounded backdrop-blur">
          CAM 0{activeCam} • LIVE
        </span>
      </div>

      <div className="absolute top-4 right-4 z-30">
        <span className="text-[10px] font-mono text-white/80 bg-black/50 px-2 py-0.5 rounded backdrop-blur">
          YOLOv8_NANO • 64 FPS
        </span>
      </div>

      {/* Video placeholder background */}
      <div className="absolute inset-0 z-0 bg-[#0a0a0a]">
        <div className="absolute inset-0 flex items-center justify-center text-white/5 font-bold text-4xl">
          NO SIGNAL
        </div>
        {/* We use a CSS gradient to simulate a grayscale camera feed depth */}
        <div className="absolute inset-0 opacity-30 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-gray-700 via-gray-900 to-black" />
      </div>

      {/* Bounding Boxes */}
      <AnimatePresence>
        {boxes.map((box) => (
          <motion.div
            key={box.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={`absolute z-10 border-2 ${box.type === 'STAFF' ? 'border-purple-500' : 'border-blue-500'}`}
            style={{
              left: `${box.x}%`,
              top: `${box.y}%`,
              width: `${box.width}%`,
              height: `${box.height}%`
            }}
          >
            {/* Target corners */}
            <div className={`absolute -top-1 -left-1 w-2 h-2 border-t-2 border-l-2 ${box.type === 'STAFF' ? 'border-purple-300' : 'border-blue-300'}`} />
            <div className={`absolute -top-1 -right-1 w-2 h-2 border-t-2 border-r-2 ${box.type === 'STAFF' ? 'border-purple-300' : 'border-blue-300'}`} />
            <div className={`absolute -bottom-1 -left-1 w-2 h-2 border-b-2 border-l-2 ${box.type === 'STAFF' ? 'border-purple-300' : 'border-blue-300'}`} />
            <div className={`absolute -bottom-1 -right-1 w-2 h-2 border-b-2 border-r-2 ${box.type === 'STAFF' ? 'border-purple-300' : 'border-blue-300'}`} />
            
            {/* Label */}
            <div className={`absolute -top-5 left-[-2px] px-1 text-[9px] font-bold text-white whitespace-nowrap
              ${box.type === 'STAFF' ? 'bg-purple-500' : 'bg-blue-500'}`}
            >
              {box.type} {box.confidence}%
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
      
      {/* Scanning laser effect */}
      <motion.div 
        className="absolute left-0 right-0 h-0.5 bg-blue-500/50 shadow-[0_0_10px_rgba(59,130,246,0.8)] z-20"
        animate={{ top: ['0%', '100%', '0%'] }}
        transition={{ duration: 4, ease: "linear", repeat: Infinity }}
      />
    </div>
  );
}
