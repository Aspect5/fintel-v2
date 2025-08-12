import React, { useMemo } from 'react';

interface StockPriceChartProps {
  series: Array<{ date?: string; timestamp?: string; close?: number; adjusted_close?: number }>;
  height?: number;
}

// Lightweight SVG line chart to avoid extra deps
const StockPriceChart: React.FC<StockPriceChartProps> = ({ series, height = 160 }) => {
  const points = useMemo(() => {
    const values = (series || [])
      .map(p => ({
        t: new Date(p.date || p.timestamp || ''),
        v: typeof p.adjusted_close === 'number' ? p.adjusted_close : (typeof p.close === 'number' ? p.close : NaN)
      }))
      .filter(p => !isNaN(p.t.getTime()) && !isNaN(p.v));
    if (values.length === 0) return { path: '', min: 0, max: 0 };
    const minV = Math.min(...values.map(p => p.v));
    const maxV = Math.max(...values.map(p => p.v));
    const pad = (maxV - minV) * 0.1 || 1;
    const yMin = minV - pad;
    const yMax = maxV + pad;
    const w = 520;
    const h = height;
    const stepX = values.length > 1 ? w / (values.length - 1) : w;
    const y = (v: number) => h - ((v - yMin) / (yMax - yMin)) * h;
    const path = values.map((p, i) => `${i === 0 ? 'M' : 'L'} ${i * stepX},${y(p.v)}`).join(' ');
    return { path, min: minV, max: maxV };
  }, [series, height]);

  if (!points.path) return null;

  return (
    <div className="bg-brand-bg p-3 rounded-lg border border-brand-border">
      <svg width={520} height={height}>
        <defs>
          <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#58A6FF" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#58A6FF" stopOpacity="0.05" />
          </linearGradient>
        </defs>
        <path d={points.path} fill="none" stroke="#58A6FF" strokeWidth={2} />
      </svg>
    </div>
  );
};

export default StockPriceChart;


