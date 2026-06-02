import { motion, HTMLMotionProps } from "framer-motion";
import { ReactNode } from "react";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  children: ReactNode;
  className?: string;
}

export default function GlassCard({ children, className = "", ...props }: GlassCardProps) {
  return (
    <motion.div
      {...props}
      transition={{ type: "spring", stiffness: 300, damping: 30, ...props.transition }}
      className={`
        relative overflow-hidden rounded-3xl backdrop-blur-[20px] 
        bg-white/60 border border-black/5 shadow-[0_8px_32px_rgba(0,0,0,0.04)] text-black/90
        dark:bg-[#1E1E1E]/40 dark:border-white/10 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] dark:text-white/90
        ${className}
      `}
    >
      {children}
    </motion.div>
  );
}
