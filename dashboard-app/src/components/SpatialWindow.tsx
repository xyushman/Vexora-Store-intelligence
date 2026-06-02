import { ReactNode } from "react";
import GlassCard from "./GlassCard";
import { HTMLMotionProps } from "framer-motion";

interface SpatialWindowProps extends HTMLMotionProps<"div"> {
  title: string;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

export default function SpatialWindow({ title, children, className = "", bodyClassName = "", ...props }: SpatialWindowProps) {
  return (
    <GlassCard
      {...props}
      className={`flex flex-col relative overflow-hidden ${className}`}
    >
      {/* Title Bar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white/40 dark:bg-black/40 border-b border-black/5 dark:border-white/10 shrink-0 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-bold tracking-widest uppercase text-black/80 dark:text-white/80">
            {title}
          </h2>
        </div>
        {/* Aesthetic Window Controls */}
        <div className="flex items-center gap-2 opacity-50 hover:opacity-100 transition-opacity">
          <div className="w-3 h-3 rounded-full bg-black/20 dark:bg-white/20 flex items-center justify-center">
            <span className="text-[8px] opacity-0 hover:opacity-100">x</span>
          </div>
          <div className="w-3 h-3 rounded-full bg-black/20 dark:bg-white/20"></div>
        </div>
      </div>

      {/* Content Area */}
      <div className={`flex-1 overflow-y-auto ${bodyClassName}`}>
        {children}
      </div>
    </GlassCard>
  );
}
