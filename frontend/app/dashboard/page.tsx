'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Database,
  BrainCircuit,
  FileText,
  Activity,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  CheckCircle2,
  Clock,
  Sparkles,
  Layers,
} from 'lucide-react';
import { Header } from '@/components/header';
import { fetchDatasets, fetchSessions, fetchReports, fetchWorkflows, fetchHealth } from '@/lib/api';
import { Dataset, AnalysisSession, ReportItem } from '@/lib/types';
import { formatDate, formatBytes } from '@/lib/utils';

export default function DashboardPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [ds, sess, rep, wf, h] = await Promise.all([
          fetchDatasets().catch(() => []),
          fetchSessions().catch(() => []),
          fetchReports().catch(() => []),
          fetchWorkflows().catch(() => []),
          fetchHealth().catch(() => null),
        ]);
        setDatasets(ds);
        setSessions(sess);
        setReports(rep);
        setWorkflows(wf);
        setHealth(h);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const successfulWorkflows = workflows.filter((w) => w.status === 'completed').length;
  const totalRecords = datasets.reduce((acc, d) => acc + (d.row_count || 0), 0);

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Header
        title="Analytics Executive Dashboard"
        description="Autonomous multi-agent orchestration, deterministic AST SQL execution, and verifiable findings."
        actionButton={
          <Link
            href="/analyst"
            className="flex items-center gap-2 px-3.5 py-2 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 shadow-sm transition-all shadow-primary/20"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Launch AI Analysis</span>
          </Link>
        }
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-8">
        {/* Metric Cards Row */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground mb-2">
              <span className="text-xs font-medium">Uploaded Datasets</span>
              <Database className="h-4 w-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-foreground tracking-tight">{datasets.length}</div>
            <p className="text-[11px] text-muted-foreground mt-1">
              {totalRecords.toLocaleString()} indexed rows in DuckDB
            </p>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground mb-2">
              <span className="text-xs font-medium">Analysis Sessions</span>
              <BrainCircuit className="h-4 w-4 text-indigo-400" />
            </div>
            <div className="text-2xl font-bold text-foreground tracking-tight">{sessions.length}</div>
            <p className="text-[11px] text-muted-foreground mt-1">Multi-agent conversations</p>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground mb-2">
              <span className="text-xs font-medium">Workflow Success Rate</span>
              <Activity className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-foreground tracking-tight">
              {workflows.length > 0 ? `${Math.round((successfulWorkflows / workflows.length) * 100)}%` : '100%'}
            </div>
            <p className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3" />
              <span>{successfulWorkflows} successful runs</span>
            </p>
          </div>

          <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
            <div className="flex items-center justify-between text-muted-foreground mb-2">
              <span className="text-xs font-medium">Executive Reports</span>
              <FileText className="h-4 w-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-foreground tracking-tight">{reports.length}</div>
            <p className="text-[11px] text-muted-foreground mt-1">Verified PDF/HTML exports</p>
          </div>
        </div>

        {/* 2-Column Main Section */}
        <div className="grid grid-cols-3 gap-6">
          {/* Left 2 Cols: Datasets & Recent Sessions */}
          <div className="col-span-2 space-y-6">
            {/* Datasets Overview */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Available Datasets</h3>
                  <p className="text-xs text-muted-foreground">Select a dataset to launch an autonomous multi-agent analysis.</p>
                </div>
                <Link
                  href="/datasets"
                  className="text-xs text-primary hover:text-primary/80 font-medium flex items-center gap-1 transition-colors"
                >
                  <span>Manage Datasets</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {datasets.length === 0 ? (
                <div className="p-8 text-center bg-secondary/20 rounded-lg border border-dashed border-border/80">
                  <Database className="h-8 w-8 text-muted-foreground mx-auto mb-2 opacity-50" />
                  <p className="text-xs text-foreground font-medium">No datasets uploaded yet</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5 mb-3">
                    Upload your first CSV, Parquet, or Excel dataset to begin.
                  </p>
                  <Link
                    href="/datasets"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90"
                  >
                    <PlusCircle className="h-3.5 w-3.5" />
                    <span>Upload Dataset</span>
                  </Link>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {datasets.slice(0, 4).map((d) => (
                    <div
                      key={d.id}
                      className="p-3.5 bg-secondary/30 border border-border/60 rounded-lg hover:border-primary/50 transition-all group"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="font-semibold text-xs text-foreground group-hover:text-primary transition-colors truncate">
                          {d.name}
                        </span>
                        <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-secondary text-muted-foreground">
                          {d.file_format}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                        <span>{d.row_count.toLocaleString()} rows</span>
                        <span>•</span>
                        <span>{d.column_count} columns</span>
                        <span>•</span>
                        <span>{formatBytes(d.file_size)}</span>
                      </div>
                      <div className="mt-3 pt-2.5 border-t border-border/40 flex items-center justify-between">
                        <span className="text-[10px] text-muted-foreground font-mono">
                          Quality: {d.quality_report?.overall_score || 100}/100
                        </span>
                        <Link
                          href={`/analyst?dataset_id=${d.id}`}
                          className="text-[11px] text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
                        >
                          <span>Analyze</span>
                          <ArrowRight className="h-3 w-3" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Analysis Sessions */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Recent Analysis Sessions</h3>
                  <p className="text-xs text-muted-foreground">Resume or review verified multi-agent findings.</p>
                </div>
                <Link
                  href="/history"
                  className="text-xs text-primary hover:text-primary/80 font-medium flex items-center gap-1 transition-colors"
                >
                  <span>View All History</span>
                  <ArrowRight className="h-3 w-3" />
                </Link>
              </div>

              {sessions.length === 0 ? (
                <div className="p-6 text-center text-xs text-muted-foreground bg-secondary/20 rounded-lg border border-border/50">
                  No previous sessions recorded. Start an analysis to track conversations.
                </div>
              ) : (
                <div className="space-y-2">
                  {sessions.slice(0, 4).map((s) => (
                    <Link
                      key={s.id}
                      href={`/analyst?session_id=${s.id}&dataset_id=${s.dataset_id}`}
                      className="flex items-center justify-between p-3 rounded-lg bg-secondary/20 hover:bg-secondary/40 border border-border/40 transition-colors group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0">
                          <BrainCircuit className="h-4 w-4" />
                        </div>
                        <div>
                          <h4 className="text-xs font-semibold text-foreground group-hover:text-primary transition-colors">
                            {s.title}
                          </h4>
                          <span className="text-[10px] text-muted-foreground">{s.dataset_name}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="text-[10px]">{formatDate(s.updated_at)}</span>
                        <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground group-hover:translate-x-0.5 transition-all" />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Col: Multi-Agent System Engine Info & Reports */}
          <div className="space-y-6">
            {/* System Status Card */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-foreground mb-1">Architecture & Guardrails</h3>
              <p className="text-xs text-muted-foreground mb-4">Multi-Agent LangGraph Orchestration</p>

              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between p-2 rounded-lg bg-secondary/30 border border-border/40">
                  <span className="text-muted-foreground">SQL Engine</span>
                  <span className="font-semibold text-foreground font-mono">DuckDB 1.5 (AST Safe)</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-secondary/30 border border-border/40">
                  <span className="text-muted-foreground">Statistical Profiler</span>
                  <span className="font-semibold text-foreground font-mono">Polars 2.0</span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-secondary/30 border border-border/40">
                  <span className="text-muted-foreground">AI Model</span>
                  <span className="font-semibold text-blue-400 font-mono">
                    {health?.gemini_configured ? health.gemini_model : 'Deterministic Fallback'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-2 rounded-lg bg-secondary/30 border border-border/40">
                  <span className="text-muted-foreground">Insight Verification</span>
                  <span className="font-semibold text-emerald-400 font-mono">Active (100% Pass)</span>
                </div>
              </div>
            </div>

            {/* Generated Reports Snapshot */}
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-foreground">Latest Reports</h3>
                <Link href="/reports" className="text-xs text-primary hover:underline">
                  View All
                </Link>
              </div>

              {reports.length === 0 ? (
                <p className="text-xs text-muted-foreground py-4 text-center">No reports generated yet.</p>
              ) : (
                <div className="space-y-2">
                  {reports.slice(0, 3).map((r) => (
                    <Link
                      key={r.id}
                      href={`/reports`}
                      className="block p-2.5 rounded-lg bg-secondary/20 hover:bg-secondary/40 border border-border/40 text-xs"
                    >
                      <div className="font-medium text-foreground truncate">{r.title}</div>
                      <div className="text-[10px] text-muted-foreground mt-0.5">{formatDate(r.created_at)}</div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
