"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Tooltip } from 'recharts';
import { useTheme } from 'next-themes';
import { useState, useEffect } from 'react';

const sentimentData = [
  { name: 'Happy', value: 45, color: '#34d399' },
  { name: 'Neutral', value: 35, color: '#60a5fa' },
  { name: 'Frustrated', value: 20, color: '#f87171' },
];

const demographicsData = [
  { subject: 'Male', A: 120, fullMark: 150 },
  { subject: 'Female', A: 98, fullMark: 150 },
  { subject: '18-24', A: 86, fullMark: 150 },
  { subject: '25-34', A: 99, fullMark: 150 },
  { subject: '35-44', A: 85, fullMark: 150 },
  { subject: '45+', A: 65, fullMark: 150 },
];

export default function ShopperInsights() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
    const interval = setInterval(() => {
      setPulse(p => p + 1);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!mounted) return null;

  return (
    <div className="h-full flex flex-col gap-4">
      <div className="flex-1 glass-panel p-4 flex flex-col">
        <h3 className="text-xs font-bold uppercase tracking-widest text-black/50 dark:text-white/50 mb-2">Live Sentiment Analysis</h3>
        <div className="flex-1 relative">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                innerRadius="60%"
                outerRadius="80%"
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: theme === 'dark' ? '#1E1E1E' : '#ffffff',
                  borderColor: theme === 'dark' ? '#333' : '#eee',
                  borderRadius: '12px',
                  boxShadow: '0 8px 30px rgba(0,0,0,0.12)'
                }} 
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Central score */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-2xl font-bold text-black/90 dark:text-white/90">82</span>
            <span className="text-[10px] uppercase tracking-wider text-green-500 font-semibold">Score</span>
          </div>
        </div>
      </div>

      <div className="flex-1 glass-panel p-4 flex flex-col">
        <h3 className="text-xs font-bold uppercase tracking-widest text-black/50 dark:text-white/50 mb-2">Real-Time Demographics</h3>
        <div className="flex-1 -mt-4">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="60%" data={demographicsData}>
              <PolarGrid stroke={theme === 'dark' ? '#333' : '#e5e7eb'} />
              <PolarAngleAxis 
                dataKey="subject" 
                tick={{ fill: theme === 'dark' ? '#888' : '#666', fontSize: 10 }} 
              />
              <Radar 
                name="Shoppers" 
                dataKey="A" 
                stroke="var(--accent-blue)" 
                fill="var(--accent-blue)" 
                fillOpacity={0.3} 
                isAnimationActive={true}
                animationDuration={1500}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: theme === 'dark' ? '#1E1E1E' : '#ffffff',
                  borderColor: theme === 'dark' ? '#333' : '#eee',
                  borderRadius: '12px'
                }} 
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
