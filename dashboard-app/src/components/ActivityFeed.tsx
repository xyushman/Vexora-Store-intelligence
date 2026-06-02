"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Activity, Camera, ArrowRight } from "lucide-react";

interface Event {
  event_id: string;
  event_type: string;
  timestamp: string;
  zone_id?: string;
  camera_id: string;
}

export default function ActivityFeed({ events }: { events: Event[] }) {
  return (
    <div className="glass-panel flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-[var(--color-glass-border)] flex items-center gap-2">
        <Activity size={18} className="text-[var(--accent-blue)]" />
        <h3 className="font-semibold tracking-wide">Live Activity</h3>
      </div>
      <div className="p-4 overflow-y-auto flex-1 flex flex-col gap-3">
        <AnimatePresence initial={false}>
          {events.slice(0, 100).map((ev, i) => (
            <motion.div
              key={ev.event_id}
              initial={{ opacity: 0, x: -20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: "auto" }}
              className="p-3 rounded-xl bg-white/5 border border-white/5 flex gap-3 text-sm"
            >
              <div className="mt-0.5 text-gray-500">
                {ev.event_type.includes("ENTER") || ev.event_type === "ENTRY" ? (
                  <ArrowRight size={14} className="text-green-400" />
                ) : ev.event_type.includes("EXIT") ? (
                  <ArrowRight size={14} className="text-red-400 rotate-180" />
                ) : (
                  <Camera size={14} className="text-purple-400" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <span className="font-medium text-gray-200">
                    {ev.event_type.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(ev.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                {ev.zone_id && (
                  <div className="text-gray-400 mt-1 text-xs">
                    Zone: <span className="text-gray-300">{ev.zone_id}</span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {events.length === 0 && (
          <div className="text-center text-gray-500 py-10">
            Waiting for activity...
          </div>
        )}
      </div>
    </div>
  );
}
