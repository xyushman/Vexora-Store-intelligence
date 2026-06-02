"use client";

import { motion } from "framer-motion";

export default function Funnel3D({ funnel }: { funnel: any[] }) {
  if (!funnel) return null;

  const maxCount = Math.max(...funnel.map(f => f.unique_visitors), 1);

  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <h3 className="font-semibold tracking-wide mb-6">Customer Journey</h3>
      
      <div className="flex-1 flex flex-col justify-center gap-4">
        {funnel.map((stage, idx) => {
          const width = `${(stage.unique_visitors / maxCount) * 100}%`;
          const prevCount = idx > 0 ? funnel[idx-1].unique_visitors : stage.unique_visitors;
          const dropoff = prevCount > 0 ? ((prevCount - stage.unique_visitors) / prevCount) * 100 : 0;
          
          return (
            <div key={stage.stage} className="relative w-full">
              {idx > 0 && dropoff > 0 && (
                <div className="absolute right-0 -top-4 text-xs text-red-400">
                  -{dropoff.toFixed(1)}% drop
                </div>
              )}
              <div className="flex items-center justify-between text-sm mb-1 text-gray-300">
                <span className="capitalize">{stage.stage.replace(/_/g, " ")}</span>
                <span className="font-bold">{stage.unique_visitors}</span>
              </div>
              <div className="w-full h-8 bg-white/5 rounded-lg overflow-hidden border border-white/5 relative">
                {/* Animated gradient bar */}
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width }}
                  transition={{ duration: 1, ease: "easeOut" }}
                  className="h-full bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-purple)] relative overflow-hidden"
                >
                  {/* Subtle shimmer effect inside the bar */}
                  <motion.div
                    animate={{ x: ["-100%", "200%"] }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                    className="absolute top-0 bottom-0 w-1/2 bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-[-20deg]"
                  />
                </motion.div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
