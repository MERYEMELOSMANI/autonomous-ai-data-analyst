'use client';

import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
  Code2,
  Clock,
  Layers,
  Database,
  X,
} from 'lucide-react';
import { EvidenceRecord } from '@/lib/types';

interface EvidenceModalProps {
  evidence: EvidenceRecord | null;
  onClose: () => void;
}

export function EvidenceModal({ evidence, onClose }: EvidenceModalProps) {
  const [copied, setCopied] = useState(false);

  if (!evidence) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(evidence.query_or_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isVerified = evidence.verification_status === 'VERIFIED';
  const isFlagged = evidence.verification_status === 'FLAGGED';

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-secondary/30">
          <div className="flex items-center gap-3">
            <div
              className={`h-8 w-8 rounded-lg flex items-center justify-center ${
                isVerified
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : isFlagged
                  ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              }`}
            >
              {isVerified ? (
                <CheckCircle2 className="h-5 w-5" />
              ) : isFlagged ? (
                <AlertTriangle className="h-5 w-5" />
              ) : (
                <XCircle className="h-5 w-5" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-foreground text-sm">Verifiable Computation Proof</h3>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${
                    isVerified
                      ? 'bg-emerald-500/20 text-emerald-300'
                      : isFlagged
                      ? 'bg-amber-500/20 text-amber-300'
                      : 'bg-rose-500/20 text-rose-300'
                  }`}
                >
                  {evidence.verification_status}
                </span>
              </div>
              <span className="text-xs text-muted-foreground font-mono">Evidence ID: {evidence.id}</span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-secondary/60 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 overflow-y-auto">
          {/* Claim statement */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
              Evaluated Statement
            </h4>
            <p className="text-sm font-medium text-foreground bg-secondary/20 p-3 rounded-lg border border-border/50">
              {evidence.claim}
            </p>
          </div>

          {/* Audit Metrics Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-secondary/30 p-3 rounded-lg border border-border/40">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                <Database className="h-3.5 w-3.5" />
                <span>Deterministic Engine</span>
              </div>
              <span className="text-xs font-semibold text-foreground font-mono uppercase">{evidence.tool}</span>
            </div>

            <div className="bg-secondary/30 p-3 rounded-lg border border-border/40">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                <Clock className="h-3.5 w-3.5" />
                <span>Execution Latency</span>
              </div>
              <span className="text-xs font-semibold text-foreground font-mono">{evidence.execution_time_ms} ms</span>
            </div>

            <div className="bg-secondary/30 p-3 rounded-lg border border-border/40">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mb-1">
                <Layers className="h-3.5 w-3.5" />
                <span>Columns Evaluated</span>
              </div>
              <span className="text-xs font-semibold text-foreground font-mono">
                {evidence.columns_involved.length > 0 ? evidence.columns_involved.join(', ') : 'All'}
              </span>
            </div>
          </div>

          {/* Traceable SQL Code */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <Code2 className="h-3.5 w-3.5" />
                <span>Traceable AST-Validated SQL Query</span>
              </div>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                <span>{copied ? 'Copied' : 'Copy SQL'}</span>
              </button>
            </div>
            <pre className="p-3 bg-black/50 border border-border/60 rounded-lg text-xs font-mono text-emerald-300 overflow-x-auto select-all">
              {evidence.query_or_code}
            </pre>
          </div>

          {/* Computed Numerical Ground Truth */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1.5">
              Exact Computed Values (Ground Truth)
            </h4>
            <div className="bg-secondary/20 p-3 rounded-lg border border-border/50 text-xs font-mono">
              <pre className="text-blue-300 overflow-x-auto">
                {JSON.stringify(evidence.computed_values, null, 2)}
              </pre>
            </div>
          </div>

          {/* Verification Notes */}
          {evidence.verification_notes && (
            <div className="bg-blue-500/10 border border-blue-500/20 p-3 rounded-lg text-xs text-blue-300">
              <span className="font-semibold block mb-0.5">Verification Auditor Notes:</span>
              {evidence.verification_notes}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border flex justify-end bg-secondary/30">
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90 transition-colors"
          >
            Close Audit Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
