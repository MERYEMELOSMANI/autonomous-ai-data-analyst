'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { Download, BarChart2, LineChart, PieChart } from 'lucide-react';
import { VisualizationSpec } from '@/lib/types';

// Dynamically import Plotly with SSR disabled
const Plot = dynamic(() => import('react-plotly.js'), {
  ssr: false,
  loading: () => (
    <div className="h-72 w-full flex items-center justify-center bg-card/40 rounded-lg border border-border animate-pulse">
      <span className="text-xs text-muted-foreground">Rendering interactive chart...</span>
    </div>
  ),
});

interface PlotlyChartProps {
  spec: VisualizationSpec;
  height?: number;
}

export function PlotlyChart({ spec, height = 340 }: PlotlyChartProps) {
  const [currentType, setCurrentType] = useState<string>(spec.chart_type);

  const rawData = spec.plotly_figure.data || [];
  const modifiedData = rawData.map((d: any) => {
    if (currentType === 'bar') {
      return { ...d, type: 'bar', mode: undefined };
    } else if (currentType === 'line') {
      return { ...d, type: 'scatter', mode: 'lines+markers' };
    } else if (currentType === 'pie') {
      return { ...d, type: 'pie', labels: d.x, values: d.y };
    }
    return d;
  });

  const layout = {
    ...spec.plotly_figure.layout,
    autosize: true,
    height,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#94a3b8', family: 'Inter, sans-serif', size: 11 },
  };

  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm hover:border-border/80 transition-all flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="text-sm font-semibold text-foreground tracking-tight">{spec.title}</h4>
          {spec.description && (
            <p className="text-xs text-muted-foreground mt-0.5">{spec.description}</p>
          )}
        </div>

        {/* Quick chart type toggler */}
        <div className="flex items-center gap-1 bg-secondary/50 p-1 rounded-lg border border-border/50">
          <button
            onClick={() => setCurrentType('bar')}
            className={`p-1.5 rounded text-xs transition-colors ${currentType === 'bar' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="Bar Chart"
          >
            <BarChart2 className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setCurrentType('line')}
            className={`p-1.5 rounded text-xs transition-colors ${currentType === 'line' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="Line Trend"
          >
            <LineChart className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setCurrentType('pie')}
            className={`p-1.5 rounded text-xs transition-colors ${currentType === 'pie' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            title="Pie Share"
          >
            <PieChart className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="w-full flex-1 min-h-[300px]">
        <Plot
          data={modifiedData}
          layout={layout}
          config={{
            responsive: true,
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </div>
  );
}
