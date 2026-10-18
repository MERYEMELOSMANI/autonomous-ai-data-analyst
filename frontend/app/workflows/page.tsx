'use client';

import React, { useEffect, useState } from 'react';
import {
  GitMerge,
  Activity,
  CheckCircle2,
  Clock,
  Layers,
  BrainCircuit,
  Database,
  BarChart2,
  ShieldCheck,
  FileCheck2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { Header } from '@/components/header';
import { fetchWorkflows, fetchWorkflowDetails } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const list = await fetchWorkflows();
        setWorkflows(list);
        if (list.length > 0) {
          const details = await fetchWorkflowDetails(list[0].id);
          setSelectedWorkflow(details);
        }
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleSelect = async (id: string) => {
    try {
      const details = await fetchWorkflowDetails(id);
      setSelectedWorkflow(details);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Header
        title="Agent Workflows & Execution Traces"
        description="Inspect LangGraph state transitions, tool invocations, step latency, and verification loops."
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Architecture Flowchart Card */}
        <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-foreground mb-1">LangGraph Multi-Agent Architecture</h3>
          <p className="text-xs text-muted-foreground mb-4">
            Deterministic state graph routing between specialized agents with bounded verification retry loops.
          </p>

          <div className="grid grid-cols-6 gap-2 text-center text-xs">
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <BrainCircuit className="h-5 w-5 text-blue-400 mx-auto mb-1.5" />
              <div className="font-semibold text-foreground">1. Supervisor</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Planning & Routing</div>
            </div>

            <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
              <Database className="h-5 w-5 text-amber-400 mx-auto mb-1.5" />
              <div className="font-semibold text-foreground">2. Data Quality</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Nulls & Outliers</div>
            </div>

            <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
              <BarChart2 className="h-5 w-5 text-indigo-400 mx-auto mb-1.5" />
              <div className="font-semibold text-foreground">3. Data Analysis</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">DuckDB Safe SQL</div>
            </div>

            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
              <ShieldCheck className="h-5 w-5 text-emerald-400 mx-auto mb-1.5" />
              <div className="font-semibold text-foreground">4. Verification</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Exact Proof Check</div>
            </div>

            <div className="p-3 bg-sky-500/10 border border-sky-500/20 rounded-lg">
              <BarChart2 className="h-5 w-5 text-sky-400 mx-auto mb-1.5" />
              <div className="font-semibold text-foreground">5. Visualization</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Plotly Spec Engine</div>
            </div>

            <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
              <FileCheck2 className="h-5 w-5 text-purple-400 mx-auto mb-1.5" />
              <div className="font-semibold text-foreground">6. Report Agent</div>
              <div className="text-[10px] text-muted-foreground mt-0.5">Executive Synthesis</div>
            </div>
          </div>
        </div>

        {/* 2-Column Workflow Log Viewer */}
        <div className="grid grid-cols-12 gap-6">
          {/* List of Workflow Runs */}
          <div className="col-span-5 bg-card border border-border rounded-xl p-4 shadow-sm space-y-3">
            <h3 className="text-sm font-semibold text-foreground">Execution History ({workflows.length})</h3>

            {workflows.length === 0 ? (
              <p className="text-xs text-muted-foreground py-6 text-center">No workflows logged yet.</p>
            ) : (
              <div className="space-y-2 overflow-y-auto max-h-[500px]">
                {workflows.map((wf) => (
                  <div
                    key={wf.id}
                    onClick={() => handleSelect(wf.id)}
                    className={`p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                      selectedWorkflow?.id === wf.id
                        ? 'bg-primary/10 border-primary text-foreground'
                        : 'bg-secondary/20 border-border/40 hover:bg-secondary/40 text-muted-foreground'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-foreground truncate max-w-[200px]">
                        {wf.query}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono">
                        {wf.status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span>{wf.dataset_name}</span>
                      <span>{wf.duration_ms} ms</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Detailed Execution Trace */}
          <div className="col-span-7 bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
            {selectedWorkflow ? (
              <div>
                <div className="border-b border-border pb-3 mb-4 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">{selectedWorkflow.query}</h3>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      Workflow ID: {selectedWorkflow.id} • {selectedWorkflow.duration_ms} ms total
                    </span>
                  </div>
                  <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold font-mono">
                    {selectedWorkflow.status.toUpperCase()}
                  </span>
                </div>

                {/* Steps log */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Step-by-Step Node Execution
                  </h4>
                  {selectedWorkflow.steps?.map((step: any, idx: number) => (
                    <div key={idx} className="p-3 bg-secondary/30 rounded-lg border border-border/60 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-foreground">{step.agent}</span>
                        <span className="text-[10px] font-mono text-muted-foreground">{step.duration_ms} ms</span>
                      </div>
                      <p className="text-muted-foreground text-[11px]">{step.action}</p>
                      {step.output_summary && (
                        <div className="text-[10px] font-mono text-emerald-300 mt-1">
                          {step.output_summary}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground text-center py-10">Select a workflow run to view details.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
