"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import KPICards from "@/components/KPICards";
import StoreHeatmap3D from "@/components/StoreHeatmap3D";
import Funnel3D from "@/components/Funnel3D";
import ActivityFeed from "@/components/ActivityFeed";
import AnomalyAlerts from "@/components/AnomalyAlerts";
import AIAssistant from "@/components/AIAssistant";
import LiveVisionFeeds from "@/components/LiveVisionFeeds";
import ShopperInsights from "@/components/ShopperInsights";
import TrendCharts from "@/components/TrendCharts";
import ThemeToggle from "@/components/ThemeToggle";
import SpatialWindow from "@/components/SpatialWindow";
import StoreBackground3D from "@/components/StoreBackground3D";
import { motion } from "framer-motion";

export default function Dashboard() {
  const lastVisitorsRef = useRef(0);
  const [metrics, setMetrics] = useState({
    unique_visitors: 0,
    conversion_rate: 0,
    purchases: 0,
    avg_dwell_time_minutes: 0,
  });
  const [events, setEvents] = useState<any[]>([]);
  const [heatmap, setHeatmap] = useState<any>(null);
  const [funnel, setFunnel] = useState<any[]>([]);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [insights, setInsights] = useState<any>(null);
  
  const STORE_ID = "ST1008";
  const API_BASE = "http://localhost:8000";

  useEffect(() => {
    // 1. Initial Fetch of Data
    const fetchInitialData = async () => {
      try {
        const [heatmapRes, funnelRes, anomaliesRes, insightsRes] = await Promise.all([
          fetch(`${API_BASE}/stores/${STORE_ID}/heatmap`),
          fetch(`${API_BASE}/stores/${STORE_ID}/funnel`),
          fetch(`${API_BASE}/stores/${STORE_ID}/anomalies`),
          fetch(`${API_BASE}/stores/${STORE_ID}/insights`),
        ]);
        
        if (heatmapRes.ok) setHeatmap((await heatmapRes.json()).zones);
        if (funnelRes.ok) setFunnel((await funnelRes.json()).funnel);
        if (anomaliesRes.ok) setAnomalies((await anomaliesRes.json()).anomalies);
        if (insightsRes.ok) setInsights(await insightsRes.json());
      } catch (err) {
        console.error("Error fetching initial data", err);
      }
    };
    fetchInitialData();

    // 2. Setup Server-Sent Events for Live Updates
    const evtSource = new EventSource(`${API_BASE}/stores/${STORE_ID}/stream`);
    
    evtSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const newMetrics = data.metrics || {};
        
        // Process the new metrics object
        let totalDwellMs = 0;
        let zoneCount = 0;
        if (newMetrics.avg_dwell_per_zone) {
          for (const val of Object.values(newMetrics.avg_dwell_per_zone)) {
            totalDwellMs += Number(val);
            zoneCount++;
          }
        }
        const avg_dwell_time_minutes = zoneCount > 0 ? (totalDwellMs / zoneCount) / 60000 : 0;

        const nextMetrics = {
          unique_visitors: newMetrics.unique_visitors || 0,
          conversion_rate: newMetrics.conversion_rate || 0,
          purchases: Math.round((newMetrics.unique_visitors || 0) * (newMetrics.conversion_rate || 0)),
          avg_dwell_time_minutes: avg_dwell_time_minutes,
        };

        if (nextMetrics.unique_visitors > lastVisitorsRef.current) {
          setEvents((e) => [{
            event_id: Math.random().toString(),
            event_type: "VISITOR_ENTERED",
            timestamp: new Date().toISOString(),
            camera_id: "CAM_ENTRY_01"
          }, ...e]);
          lastVisitorsRef.current = nextMetrics.unique_visitors;
        }
        
        setMetrics(nextMetrics);

      } catch (err) {
        console.error("Error parsing SSE data", err);
      }
    };

    // 3. Polling for Heatmap, Funnel, and Anomalies every 5s
    const interval = setInterval(fetchInitialData, 5000);

    return () => {
      evtSource.close();
      clearInterval(interval);
    };
  }, []);

  return (
    <main className="relative w-full h-screen overflow-hidden bg-[var(--background)]">
      {/* 3D Background */}
      <StoreBackground3D />
      
      {/* UI Overlay */}
      <div className="absolute inset-0 z-10 flex flex-col p-4 md:p-8 pointer-events-none">
        
        <div className="absolute top-4 left-4 right-4 z-50 pointer-events-auto">
          <AnomalyAlerts anomalies={anomalies} />
        </div>

        {/* Floating Header Pill */}
        <motion.header 
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="mx-auto flex justify-between items-center gap-6 px-6 py-3 rounded-full bg-white/60 dark:bg-[#1E1E1E]/40 backdrop-blur-[20px] border border-black/5 dark:border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.04)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.1)] pointer-events-auto shrink-0 mb-8 z-50"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[var(--accent-blue)] flex items-center justify-center text-white font-bold">
              V
            </div>
            <h1 className="text-xl font-bold text-black/90 dark:text-white/90 tracking-tight">
              Vexora Intelligence 2.0
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/" className="text-sm font-semibold hover:text-[var(--accent-blue)] transition-colors text-black/60 dark:text-white/60">
              Home
            </Link>
            <div className="w-[1px] h-4 bg-black/10 dark:bg-white/10" />
            <ThemeToggle />
          </div>
        </motion.header>

        {/* Spatial Windows Grid */}
        <div className="flex-1 w-full flex flex-col xl:flex-row gap-6 items-stretch justify-center relative min-h-0">
          
          {/* Left Window: Real-Time Analytics & Vision */}
          <SpatialWindow 
            title="Real-Time Analytics" 
            className="w-full xl:w-[400px] shrink-0 pointer-events-auto flex flex-col"
            bodyClassName="p-4 flex flex-col gap-6 flex-1 overflow-y-auto"
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
          >
            <div className="flex flex-col gap-6">
              <KPICards metrics={metrics} />
              
              <div className="h-80 shrink-0 rounded-xl overflow-hidden shadow-lg border border-white/10 relative">
                <LiveVisionFeeds />
              </div>
              
              <TrendCharts data={[metrics]} />
              <Funnel3D funnel={funnel} />
            </div>
          </SpatialWindow>

          {/* Center Window: 3D Store Heatmap */}
          <SpatialWindow 
            title="3D Store Heatmap" 
            className="flex-1 pointer-events-auto min-h-[400px] xl:min-h-0"
            bodyClassName="relative"
            initial={{ y: 50, opacity: 0, scale: 0.95 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <StoreHeatmap3D heatmap={heatmap} />
          </SpatialWindow>

          {/* Right Window: AI & Live Activity */}
          <SpatialWindow 
            title="Vexora AI & Insights" 
            className="w-full xl:w-[400px] shrink-0 pointer-events-auto flex flex-col"
            bodyClassName="p-4 flex flex-col gap-6 flex-1 overflow-y-auto relative"
            initial={{ x: 50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div className="flex flex-col gap-6 h-full">
              <div className="h-48 shrink-0">
                <AIAssistant anomalies={anomalies} />
              </div>
              
              <div className="h-80 shrink-0">
                <ShopperInsights data={insights} />
              </div>

              <div className="flex-1 min-h-[200px]">
                <h3 className="text-xs font-bold uppercase tracking-widest text-black/50 dark:text-white/50 mb-2">Live System Activity</h3>
                <ActivityFeed events={events} />
              </div>
            </div>
          </SpatialWindow>

        </div>
      </div>
    </main>
  );
}
