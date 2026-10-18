'use client';

import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  BrainCircuit,
  Database,
  BarChart2,
  FileCheck2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { TimelineStep } from '@/lib/types';

interface AgentTimelineProps {
  steps: TimelineStep[];
  isStreaming?: boolean;
}

const AGENT_ICONS: Record<string, React.ReactNode> = {
  Supervisor: <BrainCircuit className="h-4 w-4 text-blue-400" />,
  'Data Quality Agent': <Database className="h-4 w-4 text-amber-400" />,
  'Data Analysis Agent': <BarChart2 className="h-4 w-4 text-indigo-400" />,
  'Insight Verification Agent': <ShieldCheck className="h-4 w-4 text-emerald-400" />,
  'Visualization Agent': <BarChart2 className="h-4 w-4 text-sky-400" />,
  'Report Agent': <FileCheck2 className="h-4 w-4 text-purple-400" />,
};

export function AgentTimeline({ steps, isStreaming = false }: AgentTimelineProps) {
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpandedSteps((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  if (!steps || steps.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-muted-foreground bg-card/40 rounded-xl border border-border">
        {isStreaming ? (
          <div className="flex flex-col items-center gap-2">
            <RefreshCw className="h-5 w-5 text-primary animate-spin" />
            <span>Initializing LangGraph Multi-Agent Orchestration...</span>
          </div>
        ) : (
          <span>No active workflow timeline. Run an analysis to track live agent execution.</span>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between pb-1 border-b border-border">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-foreground tracking-tight">Agent Execution Timeline</span>
          {isStreaming && (
            <span className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-ping" />
              Live SSE Stream
            </span>
          )}
        </div>
        <span className="text-[11px] text-muted-foreground font-mono">{steps.length} steps executed</span>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
        {steps.map((step, idx) => {
          const isExpanded = !!expandedSteps[step.id];
          const icon = AGENT_ICONS[step.agent] || <BrainCircuit className="h-4 w-4 text-muted-foreground" />;
          const isSuccess = step.status === 'completed';
          const isRetrying = step.status === 'retrying';

          return (
            <div key={step.id || idx} className="relative group">
              {/* Dot marker on vertical line */}
              <div
                className={`absolute -left-6 top-1 h-5 w-5 rounded-full flex items-center justify-center border-2 bg-card ${
                  isSuccess
                    ? 'border-emerald-500 text-emerald-400'
                    : isRetrying
                    ? 'border-amber-500 text-amber-400 animate-pulse'
                    : 'border-blue-500 text-blue-400 animate-spin'
                }`}
              >
                {isSuccess ? (
                  <CheckCircle2 className="h-3 w-3" />
                ) : isRetrying ? (
                  <AlertCircle className="h-3 w-3" />
                ) : (
                  <RefreshCw className="h-3 w-3" />
                )}
              </div>

              {/* Step Card */}
              <div className="bg-card/70 border border-border rounded-lg p-3 text-xs transition-all hover:border-border/80">
                <div
                  className="flex items-center justify-between cursor-pointer select-none"
                  onClick={() => toggleExpand(step.id)}
                >
                  <div className="flex items-center gap-2">
                    {icon}
                    <span className="font-semibold text-foreground">{step.agent}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {step.duration_ms !== undefined && (
                      <span className="text-[10px] text-muted-foreground font-mono flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {step.duration_ms} ms
                      </span>
                    )}
                    {isExpanded ? (
                      <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                    )}
                  </div>
                </div>

                <p className="text-muted-foreground mt-1 text-[11px]">{step.action}</p>

                {step.output_summary && (
                  <div className="mt-1.5 text-[11px] font-mono text-emerald-300 bg-emerald-500/5 px-2 py-1 rounded border border-emerald-500/15">
                    {step.output_summary}
                  </div>
                )}

                {/* Expandable Technical Details */}
                {isExpanded && step.details && (
                  <div className="mt-2.5 pt-2 border-t border-border/50 text-[10px] font-mono space-y-1.5 text-slate-300 bg-secondary/30 p-2 rounded">
                    {step.tool_name && (
                      <div>
                        <span className="text-muted-foreground">Tool invoked: </span>
                        <span className="text-blue-400">{step.tool_name}</span>
                      </div>
                    )}
                    {step.input_summary && (
                      <div>
                        <span className="text-muted-foreground">Input: </span>
                        <span>{step.input_summary}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-muted-foreground">Payload details:</span>
                      <pre className="mt-1 overflow-x-auto text-[10px] text-slate-400">
                        {JSON.stringify(step.details, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
