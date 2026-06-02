"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

export default function TrendCharts({ data }: { data: any[] }) {
  // Mock trend data since the API doesn't provide historical data directly yet,
  // we'll simulate a 7-day trend for demonstration of the component.
  const chartData = [
    { name: 'Mon', conversion: 12, visitors: 150 },
    { name: 'Tue', conversion: 15, visitors: 200 },
    { name: 'Wed', conversion: 10, visitors: 120 },
    { name: 'Thu', conversion: 18, visitors: 250 },
    { name: 'Fri', conversion: 22, visitors: 300 },
    { name: 'Sat', conversion: 25, visitors: 400 },
    { name: 'Sun', conversion: Math.max(10, data[0]?.conversion_rate * 100 || 0), visitors: Math.max(50, data[0]?.unique_visitors || 0) },
  ];

  return (
    <div className="glass-panel p-6 h-full flex flex-col">
      <h3 className="font-semibold tracking-wide mb-6">Conversion Trend</h3>
      <div className="flex-1 w-full min-h-[250px]" style={{ minWidth: 0, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
            <XAxis dataKey="name" stroke="rgba(128,128,128,0.5)" tick={{ fill: 'rgba(128,128,128,0.8)', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis stroke="rgba(128,128,128,0.5)" tick={{ fill: 'rgba(128,128,128,0.8)', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--background)', backdropFilter: 'blur(10px)', border: '1px solid var(--color-glass-border)', borderRadius: '12px' }}
              itemStyle={{ color: 'var(--foreground)' }}
            />
            <Line 
              type="monotone" 
              dataKey="conversion" 
              stroke="url(#colorGradient)" 
              strokeWidth={4}
              dot={false}
              activeDot={{ r: 6, fill: 'var(--accent-blue)' }}
            />
            <defs>
              <linearGradient id="colorGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="5%" stopColor="var(--accent-purple)" />
                <stop offset="95%" stopColor="var(--accent-blue)" />
              </linearGradient>
            </defs>
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
