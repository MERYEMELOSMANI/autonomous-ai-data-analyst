'use client';

import React, { useEffect, useState } from 'react';
import { Settings, Key, ShieldCheck, Database, CheckCircle2, AlertCircle, Save, Eye, EyeOff } from 'lucide-react';
import { Header } from '@/components/header';
import { fetchSettings, updateSettings } from '@/lib/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gemini-2.5-flash');
  const [observability, setObservability] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchSettings();
        setSettings(data);
        if (data.gemini_model) {
          setSelectedModel(data.gemini_model);
        }
        setObservability(data.observability_enabled);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(false);
    try {
      const payload: any = {
        gemini_model: selectedModel,
        observability_enabled: observability,
      };
      if (apiKey.trim()) {
        payload.gemini_api_key = apiKey.trim();
      }
      const updated = await updateSettings(payload);
      setSavedSuccess(true);
      setApiKey('');
      setSettings((prev: any) => ({ ...prev, ...updated }));
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to update settings');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Header
        title="Settings & System Configurations"
        description="Configure AI providers, Google Gemini API keys, models, and observability tracking."
      />

      <div className="flex-1 overflow-y-auto p-8 max-w-4xl space-y-6">
        <form onSubmit={handleSave} className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-6">
          <div className="border-b border-border pb-4">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Key className="h-4 w-4 text-primary" />
              <span>AI Model Configuration (Google Gemini)</span>
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              The application uses Google Gemini with deterministic DuckDB AST validation and fallback heuristics.
            </p>
          </div>

          {/* API Key */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-foreground">Gemini API Key</label>
              <span className="text-[11px] font-mono">
                Status:{' '}
                {settings?.gemini_configured ? (
                  <span className="text-emerald-400 font-semibold">Configured & Active</span>
                ) : (
                  <span className="text-amber-400 font-semibold">Using Offline / Deterministic Engine</span>
                )}
              </span>
            </div>
            <div className="relative flex items-center">
              <input
                type={showKey ? 'text' : 'password'}
                placeholder={settings?.gemini_configured ? '••••••••••••••••••••••••••••••••' : 'Enter AI Studio Gemini API Key (e.g. AIzaSy...)'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full bg-secondary/30 border border-border rounded-lg pl-3 pr-10 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary font-mono"
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 text-muted-foreground hover:text-foreground"
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Never hardcoded. Stored in memory / .env file only. Free tier keys available at Google AI Studio.
            </p>
          </div>

          {/* Model selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-foreground">Active Model Architecture</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-secondary/30 border border-border rounded-lg px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="gemini-2.5-flash">Gemini 2.5 Flash (Recommended — High speed & analytical reasoning)</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro (Deep reasoning & complex multi-agent steps)</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash (Lightweight)</option>
            </select>
          </div>

          {/* Observability Toggle */}
          <div className="pt-2 border-t border-border flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-foreground">Langfuse Agent Observability</div>
              <p className="text-[11px] text-muted-foreground">Log agent execution traces, step latencies, and token usage.</p>
            </div>
            <input
              type="checkbox"
              checked={observability}
              onChange={(e) => setObservability(e.target.checked)}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary bg-secondary"
            />
          </div>

          {savedSuccess && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-lg text-xs flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>Settings updated successfully!</span>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              className="flex items-center gap-1.5 px-4 py-2 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 transition-colors shadow-sm"
            >
              <Save className="h-3.5 w-3.5" />
              <span>Save Configurations</span>
            </button>
          </div>
        </form>

        {/* System Diagnostics Card */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm space-y-4">
          <div className="border-b border-border pb-3">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>System & Sandbox Diagnostics</span>
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-secondary/30 rounded-lg border border-border/50">
              <span className="text-muted-foreground block text-[11px]">Database Engine</span>
              <span className="font-semibold text-foreground font-mono mt-0.5 block">
                {settings?.database_url || 'SQLite / PostgreSQL'}
              </span>
            </div>
            <div className="p-3 bg-secondary/30 rounded-lg border border-border/50">
              <span className="text-muted-foreground block text-[11px]">SQL AST Sandbox</span>
              <span className="font-semibold text-emerald-400 font-mono mt-0.5 block">
                sqlglot Read-Only AST Enforced
              </span>
            </div>
            <div className="p-3 bg-secondary/30 rounded-lg border border-border/50">
              <span className="text-muted-foreground block text-[11px]">Max Dataset Upload Limit</span>
              <span className="font-semibold text-foreground font-mono mt-0.5 block">
                {settings?.max_upload_size_mb || 100} MB
              </span>
            </div>
            <div className="p-3 bg-secondary/30 rounded-lg border border-border/50">
              <span className="text-muted-foreground block text-[11px]">Supported Formats</span>
              <span className="font-semibold text-foreground font-mono mt-0.5 block">
                CSV, Parquet, Excel (.xlsx, .xls)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
