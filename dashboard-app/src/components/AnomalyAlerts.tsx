"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";

export default function AnomalyAlerts({ anomalies }: { anomalies: any[] }) {
  if (!anomalies || anomalies.length === 0) return null;

  return (
    <div className="fixed top-28 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 w-full max-w-lg pointer-events-none">
      <AnimatePresence>
        {anomalies.map((anom, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: -20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="pointer-events-auto bg-red-500/20 backdrop-blur-xl border border-red-500/50 p-4 rounded-2xl shadow-[0_0_30px_rgba(255,59,48,0.2)] flex items-start gap-4"
          >
            <div className="p-2 bg-red-500/20 rounded-full animate-pulse">
              <AlertTriangle className="text-red-400" size={24} />
            </div>
            <div>
              <h4 className="text-red-400 font-bold tracking-wide">Anomaly: {anom.type}</h4>
              <p className="text-gray-200 text-sm mt-1">{anom.suggested_action}</p>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
