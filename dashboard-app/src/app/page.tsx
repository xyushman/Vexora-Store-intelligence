"use client";

import Link from "next/link";
import { ArrowRight, Activity, BarChart3, Users, Sparkles } from "lucide-react";
import { motion, useScroll, useTransform } from "framer-motion";
import AppleScrollScene from "@/components/AppleScrollScene";
import ThemeToggle from "@/components/ThemeToggle";
import { useRef } from "react";
import GlassCard from "@/components/GlassCard";
import SpatialWindow from "@/components/SpatialWindow";

export default function LandingPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });

  // Hero Section Transforms
  const heroOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  const heroY = useTransform(scrollYProgress, [0, 0.2], [0, -100]);
  const heroScale = useTransform(scrollYProgress, [0, 0.2], [1, 0.9]);
  const heroBlur = useTransform(scrollYProgress, [0, 0.2], ["blur(0px)", "blur(10px)"]);

  // Features Section Transforms
  const featuresOpacity = useTransform(scrollYProgress, [0.2, 0.35, 0.55, 0.7], [0, 1, 1, 0]);
  const featuresY = useTransform(scrollYProgress, [0.2, 0.35, 0.55, 0.7], [100, 0, 0, -100]);
  const featuresScale = useTransform(scrollYProgress, [0.2, 0.35, 0.55, 0.7], [0.9, 1, 1, 0.9]);

  // CTA Section Transforms
  const ctaOpacity = useTransform(scrollYProgress, [0.7, 0.85], [0, 1]);
  const ctaY = useTransform(scrollYProgress, [0.7, 0.85], [100, 0]);
  const ctaScale = useTransform(scrollYProgress, [0.7, 0.85], [0.9, 1]);

  return (
    <div ref={containerRef} className="relative min-h-[350vh] bg-[var(--background)]">
      {/* Dynamic Background */}
      <div className="absolute inset-0 bg-grid-black/[0.02] dark:bg-grid-white/[0.02] bg-[size:50px_50px]" />
      <div className="absolute h-full w-full bg-[var(--background)] [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />

      {/* Fixed 3D Canvas Background */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 2 }}>
        <AppleScrollScene />
      </motion.div>

      {/* Navigation (Floating Pill) */}
      <motion.nav
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="fixed top-6 left-1/2 -translate-x-1/2 w-[90%] max-w-5xl flex justify-between items-center z-50 px-6 py-3 rounded-full bg-white/60 dark:bg-[#1E1E1E]/40 backdrop-blur-[20px] border border-black/5 dark:border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.04)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-[var(--accent-blue)] flex items-center justify-center text-white font-bold">
            V
          </div>
          <span className="font-bold text-xl tracking-tight text-black/90 dark:text-white/90">Vexora</span>
        </div>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <div className="w-[1px] h-4 bg-black/10 dark:bg-white/10" />
          <Link
            href="/dashboard"
            className="px-5 py-2 rounded-full bg-black/90 dark:bg-white/90 text-white dark:text-black font-semibold text-sm hover:scale-105 transition-transform shadow-lg"
          >
            Go to Dashboard
          </Link>
        </div>
      </motion.nav>

      {/* Scrollable Content Overlays */}
      <div className="relative z-10 w-full flex flex-col items-center justify-start pointer-events-none pt-[30vh]">

        {/* Section 1: Hero */}
        <motion.div
          style={{ opacity: heroOpacity, y: heroY, scale: heroScale, filter: heroBlur }}
          className="fixed top-[30vh] w-full flex flex-col items-center justify-center text-center px-4"
        >
          <GlassCard
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm text-[var(--accent-blue)] font-semibold mb-8"
          >
            <Sparkles size={16} /> Vexora Intelligence 2.0
          </GlassCard>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-6xl md:text-8xl font-extrabold tracking-tight mb-6 max-w-5xl bg-clip-text text-transparent bg-gradient-to-b from-gray-900 to-gray-400 dark:from-white dark:to-gray-500 leading-tight"
          >
            Spatial Intelligence. <br /> Reimagined.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 0.8 }}
            className="text-xl text-gray-500 max-w-2xl leading-relaxed"
          >
            Scroll down to explore the digital twin of your store.
          </motion.p>
        </motion.div>

        {/* Section 2: Features */}
        <motion.div
          style={{ opacity: featuresOpacity, y: featuresY, scale: featuresScale }}
          className="fixed top-[20vh] w-full flex flex-col items-center justify-center px-4"
        >
          <h2 className="text-4xl md:text-6xl font-bold mb-16 text-black/90 dark:text-white/90 text-center tracking-tight">
            Powerful Analytics at every angle.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl w-full">
            <FeatureCard
              icon={<BarChart3 className="text-[var(--accent-purple)] w-8 h-8" />}
              title="Real-Time Analytics"
              desc="Live tracking of store conversions, dwell times, and queue depths."
            />
            <FeatureCard
              icon={<Users className="text-[var(--accent-blue)] w-8 h-8" />}
              title="3D Heatmaps"
              desc="Visualize exactly where customers spend their time on the floor."
            />
            <FeatureCard
              icon={<Sparkles className="text-[var(--accent-green)] w-8 h-8" />}
              title="AI Detection"
              desc="Staff vs Customer classification powered by Gemini Vision."
            />
          </div>
        </motion.div>

        {/* Section 3: CTA */}
        <motion.div
          style={{ opacity: ctaOpacity, y: ctaY, scale: ctaScale }}
          className="fixed top-[40vh] w-full flex flex-col items-center justify-center text-center px-4 pointer-events-auto"
        >
          <h2 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-10 text-black/90 dark:text-white/90">
            Ready to upgrade?
          </h2>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="/dashboard"
              className="group relative inline-flex items-center justify-center gap-3 px-12 py-6 bg-black text-white dark:bg-white dark:text-black font-bold rounded-full overflow-hidden shadow-2xl"
            >
              <span className="relative flex items-center gap-3 text-xl">
                Launch Dashboard <ArrowRight size={24} className="group-hover:translate-x-1 transition-transform" />
              </span>
            </Link>
          </motion.div>
        </motion.div>

      </div>
    </div>
  );
}

function FeatureCard({ icon, title, desc }: { icon: React.ReactNode, title: string, desc: string }) {
  return (
    <SpatialWindow
      title={title}
      className="pointer-events-auto shadow-2xl h-[280px]"
      bodyClassName="p-8 flex flex-col items-center text-center justify-center h-full"
      whileHover={{ y: -10, scale: 1.02 }}
    >
      <div className="p-4 rounded-2xl bg-black/5 dark:bg-white/5 mb-6 shadow-sm border border-black/5 dark:border-white/10">
        {icon}
      </div>
      <p className="text-gray-500 dark:text-gray-400 text-lg leading-relaxed">{desc}</p>
    </SpatialWindow>
  );
}
