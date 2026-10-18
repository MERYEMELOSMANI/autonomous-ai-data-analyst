'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { FileText, Download, ExternalLink, ShieldCheck, Printer, Calendar, Database } from 'lucide-react';
import { Header } from '@/components/header';
import { fetchReports, getReportHtmlUrl } from '@/lib/api';
import { ReportItem } from '@/lib/types';
import { formatDate } from '@/lib/utils';

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchReports();
        setReports(data);
        if (data.length > 0) {
          setSelectedReport(data[0]);
        }
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Header
        title="Executive Research & Business Reports"
        description="Structured reports synthesized by the Report Agent, verifiable against DuckDB records, exportable to HTML & PDF."
      />

      <div className="flex-1 overflow-hidden grid grid-cols-12 p-8 gap-6">
        {/* Reports List */}
        <div className="col-span-4 bg-card border border-border rounded-xl p-4 shadow-sm flex flex-col h-full overflow-hidden">
          <h3 className="text-sm font-semibold text-foreground mb-3">Generated Reports ({reports.length})</h3>

          <div className="flex-1 overflow-y-auto space-y-2">
            {reports.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-8">
                No reports compiled yet. Save an analysis in the AI Analyst workspace to generate a report.
              </p>
            ) : (
              reports.map((r) => (
                <div
                  key={r.id}
                  onClick={() => setSelectedReport(r)}
                  className={`p-3.5 rounded-lg border text-xs cursor-pointer transition-all ${
                    selectedReport?.id === r.id
                      ? 'bg-primary/10 border-primary text-foreground'
                      : 'bg-secondary/20 border-border/40 hover:bg-secondary/40 text-muted-foreground'
                  }`}
                >
                  <h4 className="font-semibold text-foreground truncate">{r.title}</h4>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-1">
                    <Calendar className="h-3 w-3" />
                    <span>{formatDate(r.created_at)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Selected Report Viewer */}
        <div className="col-span-8 bg-card border border-border rounded-xl p-6 shadow-sm flex flex-col h-full overflow-y-auto space-y-6">
          {selectedReport ? (
            <div>
              {/* Header actions */}
              <div className="border-b border-border pb-4 mb-6 flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-bold text-foreground">{selectedReport.title}</h2>
                  <div className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                    <span>Generated: {formatDate(selectedReport.created_at)}</span>
                    <span>•</span>
                    <span className="text-emerald-400 font-medium">All Claims Deterministically Audited</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <a
                    href={getReportHtmlUrl(selectedReport.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 transition-colors shadow-sm"
                  >
                    <Printer className="h-3.5 w-3.5" />
                    <span>Print / PDF Export</span>
                    <ExternalLink className="h-3 w-3 ml-0.5 opacity-70" />
                  </a>
                </div>
              </div>

              {/* Sections */}
              <div className="space-y-6 text-xs text-foreground">
                <div>
                  <h3 className="font-semibold text-sm uppercase tracking-wider text-primary mb-2">
                    1. Executive Summary
                  </h3>
                  <p className="bg-secondary/30 p-4 rounded-xl border border-border/60 leading-relaxed">
                    {selectedReport.executive_summary}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold text-sm uppercase tracking-wider text-primary mb-2">
                    2. Analysis Objective & Scope
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">{selectedReport.objective}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-sm uppercase tracking-wider text-primary mb-2">
                    3. Analytical Methodology
                  </h3>
                  <p className="text-muted-foreground leading-relaxed">{selectedReport.methodology}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-sm uppercase tracking-wider text-primary mb-2">
                    4. Verified Findings
                  </h3>
                  <div className="space-y-2">
                    {selectedReport.findings?.map((f, i) => (
                      <div key={i} className="p-3 bg-secondary/20 rounded-lg border border-border/50 space-y-1">
                        <div className="font-semibold text-foreground flex items-center gap-2">
                          <ShieldCheck className="h-4 w-4 text-emerald-400" />
                          <span>{f.title}</span>
                        </div>
                        <p className="text-muted-foreground text-[11px]">{f.description}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-sm uppercase tracking-wider text-primary mb-2">
                    5. Analytical Limitations & Guardrails
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    {selectedReport.limitations?.map((lim, i) => (
                      <li key={i}>{lim}</li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h3 className="font-semibold text-sm uppercase tracking-wider text-primary mb-2">
                    6. Conclusions
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    {selectedReport.conclusions?.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-20 text-xs text-muted-foreground">
              Select a report from the left panel to inspect full narrative findings.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
