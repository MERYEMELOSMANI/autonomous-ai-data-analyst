'use client';

import React, { useEffect, useState, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Send,
  Database,
  BrainCircuit,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileText,
  Search,
  RefreshCw,
  Plus,
  BarChart2,
  Info,
} from 'lucide-react';
import { Header } from '@/components/header';
import { PlotlyChart } from '@/components/plotly-chart';
import { AgentTimeline } from '@/components/agent-timeline';
import { EvidenceModal } from '@/components/evidence-modal';
import {
  fetchDatasets,
  fetchSessions,
  fetchSessionById,
  createSession,
  getStreamUrl,
  createReport,
} from '@/lib/api';
import {
  Dataset,
  AnalysisSession,
  AnalysisMessage,
  EvidenceRecord,
  VisualizationSpec,
  TimelineStep,
} from '@/lib/types';
import { formatDate } from '@/lib/utils';

const SUGGESTED_QUERIES = [
  'What are the main patterns and summary statistics in this dataset?',
  'Compare total performance grouped by top categories.',
  'Analyze correlations and identify unusual outliers.',
  'What factors are associated with customer churn or transactions?',
  'Calculate key metrics and breakdown distributions.',
];

function AnalystWorkspaceContent() {
  const searchParams = useSearchParams();
  const initialDatasetId = searchParams.get('dataset_id');
  const initialSessionId = searchParams.get('session_id');

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(initialDatasetId || '');
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [currentSession, setCurrentSession] = useState<AnalysisSession | null>(null);

  const [inputQuery, setInputQuery] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTimeline, setActiveTimeline] = useState<TimelineStep[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceRecord | null>(null);
  const [selectedViz, setSelectedViz] = useState<VisualizationSpec[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load initial data
  useEffect(() => {
    async function init() {
      const dsList = await fetchDatasets().catch(() => []);
      setDatasets(dsList);

      const targetDsId = initialDatasetId || (dsList.length > 0 ? dsList[0].id : '');
      setSelectedDatasetId(targetDsId);

      const sessList = await fetchSessions().catch(() => []);
      setSessions(sessList);

      if (initialSessionId) {
        loadSession(initialSessionId);
      } else if (targetDsId) {
        // Create or select existing session for dataset
        const existing = sessList.find((s) => s.dataset_id === targetDsId);
        if (existing) {
          loadSession(existing.id);
        } else {
          startNewSession(targetDsId);
        }
      }
    }
    init();
  }, [initialDatasetId, initialSessionId]);

  const loadSession = async (sessId: string) => {
    try {
      const sess = await fetchSessionById(sessId);
      setCurrentSession(sess);
      setSelectedDatasetId(sess.dataset_id);

      // Load latest message's timeline and viz
      const lastAssistant = [...sess.messages].reverse().find((m) => m.role === 'assistant');
      if (lastAssistant) {
        setActiveTimeline(lastAssistant.timeline || []);
        setSelectedViz(lastAssistant.visualizations || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const startNewSession = async (dsId: string) => {
    try {
      const newSess = await createSession(dsId);
      setSessions((prev) => [newSess, ...prev]);
      setCurrentSession(newSess);
      setActiveTimeline([]);
      setSelectedViz([]);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDatasetChange = (newDsId: string) => {
    setSelectedDatasetId(newDsId);
    startNewSession(newDsId);
  };

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputQuery.trim() || !selectedDatasetId || isStreaming) return;

    const userText = inputQuery.trim();
    setInputQuery('');

    // Optimistically append user message
    const tempUserMsg: AnalysisMessage = {
      id: `usr_${Date.now()}`,
      role: 'user',
      content: userText,
      timestamp: new Date().toISOString(),
    };

    setCurrentSession((prev) => {
      if (!prev) return null;
      return {
        ...prev,
        messages: [...prev.messages, tempUserMsg],
      };
    });

    // Start SSE stream
    setIsStreaming(true);
    setActiveTimeline([]);

    const streamUrl = getStreamUrl(selectedDatasetId, userText, currentSession?.id);
    const eventSource = new EventSource(streamUrl);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);

        if (payload.event === 'step_complete') {
          setActiveTimeline((prev) => [...prev, payload.step]);
        } else if (payload.event === 'workflow_finished') {
          // Stream completed
          const assistantMsg: AnalysisMessage = {
            id: `asst_${Date.now()}`,
            role: 'assistant',
            content: payload.final_response,
            evidence: payload.evidence,
            visualizations: payload.visualizations,
            timeline: payload.timeline,
            status: 'completed',
            timestamp: new Date().toISOString(),
          };

          setCurrentSession((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              messages: [...prev.messages, assistantMsg],
            };
          });

          setSelectedViz(payload.visualizations || []);
          setActiveTimeline(payload.timeline || []);
          setIsStreaming(false);
          eventSource.close();
        } else if (payload.event === 'workflow_error') {
          alert(`Workflow error: ${payload.error}`);
          setIsStreaming(false);
          eventSource.close();
        }
      } catch (err) {
        console.error('Error parsing SSE event', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('EventSource connection error', err);
      setIsStreaming(false);
      eventSource.close();
    };
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, isStreaming]);

  const activeDataset = datasets.find((d) => d.id === selectedDatasetId);

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Header
        title="Autonomous AI Analyst Workspace"
        description="3-Panel Interactive Analytics Environment with Live Agent Orchestration & Verifiable Proof."
        datasetName={activeDataset?.name}
        actionButton={
          <div className="flex items-center gap-2">
            <select
              value={selectedDatasetId}
              onChange={(e) => handleDatasetChange(e.target.value)}
              className="bg-secondary/70 border border-border text-foreground text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-primary font-medium"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count.toLocaleString()} rows)
                </option>
              ))}
            </select>

            <button
              onClick={() => selectedDatasetId && startNewSession(selectedDatasetId)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-secondary text-foreground text-xs font-medium rounded-lg hover:bg-secondary/80 border border-border transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Session</span>
            </button>
          </div>
        }
      />

      {/* 3-Panel Main Layout */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* ================= LEFT PANEL: CHAT & HISTORY (3 cols) ================= */}
        <div className="col-span-3 border-r border-border bg-sidebar/50 flex flex-col h-full overflow-hidden">
          {/* Conversation History List */}
          <div className="p-3 border-b border-border bg-sidebar flex items-center justify-between text-xs">
            <span className="font-semibold text-muted-foreground uppercase tracking-wider text-[11px]">
              Chat & Context
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">
              {currentSession?.messages.length || 0} messages
            </span>
          </div>

          {/* Messages scroll area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {(!currentSession || currentSession.messages.length === 0) ? (
              <div className="text-center py-8 text-xs text-muted-foreground space-y-3">
                <BrainCircuit className="h-8 w-8 text-muted-foreground mx-auto opacity-40" />
                <p>Ask any analytical question about this dataset.</p>
                <div className="text-left space-y-1.5 mt-4">
                  <span className="text-[10px] uppercase font-semibold text-muted-foreground tracking-wider block">
                    Example Presets:
                  </span>
                  {SUGGESTED_QUERIES.slice(0, 3).map((q, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setInputQuery(q);
                      }}
                      className="w-full text-left p-2 rounded-lg bg-secondary/30 hover:bg-secondary border border-border/40 text-[11px] text-slate-300 transition-colors block"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              currentSession.messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`text-xs space-y-1.5 ${
                    msg.role === 'user' ? 'text-right' : 'text-left'
                  }`}
                >
                  <div
                    className={`inline-block p-3 rounded-xl max-w-[90%] text-left ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground font-medium rounded-br-none shadow-sm shadow-primary/20'
                        : 'bg-card border border-border text-foreground rounded-bl-none shadow-sm'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 opacity-70 text-[10px]">
                      {msg.role === 'user' ? <span>You</span> : <span>AI Multi-Agent System</span>}
                      <span>•</span>
                      <span>{formatDate(msg.timestamp)}</span>
                    </div>
                    <div className="whitespace-pre-line leading-relaxed">{msg.content}</div>

                    {/* Evidence Inspector Pills on Assistant Messages */}
                    {msg.evidence && msg.evidence.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-border/50 flex flex-wrap gap-1.5">
                        {msg.evidence.map((ev) => (
                          <button
                            key={ev.id}
                            onClick={() => setSelectedEvidence(ev)}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-secondary/80 hover:bg-secondary text-[10px] text-blue-300 border border-blue-400/30 transition-all font-mono"
                          >
                            <ShieldCheck className="h-3 w-3 text-emerald-400" />
                            <span>Inspect Evidence ({ev.id})</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {isStreaming && (
              <div className="flex items-center gap-2 p-3 bg-secondary/30 rounded-xl text-xs text-primary animate-pulse">
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Multi-agent workflow executing in background...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat Input Box */}
          <form onSubmit={handleSubmit} className="p-3 border-t border-border bg-card">
            <div className="relative flex items-center">
              <input
                type="text"
                placeholder={
                  activeDataset
                    ? `Ask anything about "${activeDataset.name}"...`
                    : 'Select a dataset to begin...'
                }
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                disabled={isStreaming || !selectedDatasetId}
                className="w-full bg-secondary/40 border border-border rounded-xl pl-3.5 pr-10 py-2.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputQuery.trim() || isStreaming || !selectedDatasetId}
                className="absolute right-2 p-1.5 rounded-lg bg-primary text-primary-foreground disabled:opacity-30 disabled:pointer-events-none hover:bg-primary/90 transition-colors"
              >
                <Send className="h-3.5 w-3.5" />
              </button>
            </div>
          </form>
        </div>

        {/* ================= CENTER PANEL: VISUALIZATIONS & FINDINGS (5 cols) ================= */}
        <div className="col-span-5 border-r border-border bg-background flex flex-col h-full overflow-hidden">
          <div className="p-3 border-b border-border bg-card/40 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <BarChart2 className="h-4 w-4 text-blue-400" />
              <span className="font-semibold text-foreground">Interactive Findings & Charts</span>
            </div>
            {selectedViz.length > 0 && (
              <button
                onClick={async () => {
                  if (currentSession && selectedDatasetId) {
                    await createReport(selectedDatasetId, currentSession.id);
                    alert('Executive Report compiled! View it on the Reports page.');
                  }
                }}
                className="text-[11px] text-primary hover:underline flex items-center gap-1 font-medium"
              >
                <FileText className="h-3.5 w-3.5" />
                <span>Save to Report</span>
              </button>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            {selectedViz.length === 0 ? (
              <div className="p-10 text-center text-xs text-muted-foreground bg-card/30 rounded-xl border border-dashed border-border flex flex-col items-center justify-center min-h-[300px]">
                <BarChart2 className="h-10 w-10 text-muted-foreground mb-3 opacity-30" />
                <h4 className="font-medium text-foreground text-sm">Visualizations will appear here</h4>
                <p className="max-w-xs mt-1 text-muted-foreground">
                  When the Visualization Agent generates interactive Plotly figures, they will render here with full zoom, hover inspection, and chart type toggling.
                </p>
              </div>
            ) : (
              selectedViz.map((spec) => (
                <PlotlyChart key={spec.id} spec={spec} height={320} />
              ))
            )}

            {/* Quick Evidence Explorer Cards */}
            {currentSession && currentSession.messages.length > 0 && (
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-semibold text-foreground tracking-tight flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  <span>Verifiable Quantitative Statements</span>
                </h4>

                {currentSession.messages
                  .filter((m) => m.evidence && m.evidence.length > 0)
                  .flatMap((m) => m.evidence || [])
                  .map((ev) => (
                    <div
                      key={ev.id}
                      className="p-3.5 bg-card border border-border/80 rounded-xl text-xs space-y-2 hover:border-border transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono font-semibold">
                          {ev.verification_status}
                        </span>
                        <span className="text-[10px] text-muted-foreground font-mono">
                          {ev.execution_time_ms} ms via {ev.tool}
                        </span>
                      </div>

                      <p className="font-medium text-foreground">{ev.claim}</p>

                      <div className="flex items-center justify-between pt-1">
                        <span className="text-[10px] text-muted-foreground font-mono">ID: {ev.id}</span>
                        <button
                          onClick={() => setSelectedEvidence(ev)}
                          className="text-[11px] text-blue-400 hover:text-blue-300 font-medium hover:underline"
                        >
                          Inspect Exact SQL Proof →
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>

        {/* ================= RIGHT PANEL: AGENT TIMELINE (4 cols) ================= */}
        <div className="col-span-4 bg-sidebar/30 flex flex-col h-full overflow-hidden">
          <div className="p-3 border-b border-border bg-sidebar flex items-center justify-between text-xs">
            <span className="font-semibold text-muted-foreground uppercase tracking-wider text-[11px]">
              Multi-Agent Orchestrator
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">LangGraph State Machine</span>
          </div>

          <div className="flex-1 overflow-y-auto p-5">
            <AgentTimeline steps={activeTimeline} isStreaming={isStreaming} />
          </div>
        </div>
      </div>

      {/* Inspect Evidence Modal */}
      <EvidenceModal
        evidence={selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
      />
    </div>
  );
}

export default function AnalystWorkspacePage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center bg-background text-xs text-muted-foreground">
          Loading AI Analyst Workspace...
        </div>
      }
    >
      <AnalystWorkspaceContent />
    </Suspense>
  );
}
