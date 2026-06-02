"use client";

import { motion } from "framer-motion";
import { Users, ShoppingBag, Clock, Percent } from "lucide-react";
import GlassCard from "./GlassCard";

interface KPIProps {
  metrics: {
    unique_visitors: number;
    conversion_rate: number;
    purchases: number;
    avg_dwell_time_minutes: number;
  };
}

export default function LiveKPI({ metrics }: KPIProps) {
  const cards = [
    {
      title: "Total Visitors",
      value: metrics.unique_visitors,
      icon: Users,
      color: "var(--accent-blue)",
    },
    {
      title: "Conversion Rate",
      value: `${(metrics.conversion_rate * 100).toFixed(1)}%`,
      icon: Percent,
      color: "var(--accent-green)",
    },
    {
      title: "Purchases",
      value: metrics.purchases || 0,
      icon: ShoppingBag,
      color: "var(--accent-purple)",
    },
    {
      title: "Avg Dwell Time",
      value: `${metrics.avg_dwell_time_minutes?.toFixed(1) || 0}m`,
      icon: Clock,
      color: "var(--accent-red)",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {cards.map((card, idx) => (
        <GlassCard
          key={card.title}
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          whileHover={{ scale: 1.02, y: -4 }}
          transition={{ delay: idx * 0.1 }}
          className="p-6 flex flex-col justify-between"
        >
          <div className="absolute -right-4 -top-4 opacity-10 pointer-events-none">
            <card.icon size={120} color={card.color} />
          </div>
          <div className="flex items-center gap-3 mb-6">
            <div
              className="p-3 rounded-2xl shadow-sm border border-black/5 dark:border-white/10 backdrop-blur-md"
              style={{ backgroundColor: `${card.color}15` }}
            >
              <card.icon size={22} color={card.color} />
            </div>
            <h3 className="text-black/60 dark:text-white/60 font-medium tracking-wide text-sm uppercase">
              {card.title}
            </h3>
          </div>
          <motion.div
            key={card.value} // re-animates when value changes
            initial={{ scale: 1.1, opacity: 0.8 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-5xl font-extrabold tracking-tight text-black/90 dark:text-white/90"
          >
            {card.value}
          </motion.div>
        </GlassCard>
      ))}
    </div>
  );
}
