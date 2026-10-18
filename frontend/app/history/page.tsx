'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { History, Search, BrainCircuit, ArrowRight, Database, Calendar } from 'lucide-react';
import { Header } from '@/components/header';
import { fetchSessions } from '@/lib/api';
import { AnalysisSession } from '@/lib/types';
import { formatDate } from '@/lib/utils';

export default function HistoryPage() {
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchSessions();
        setSessions(data);
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  const filteredSessions = sessions.filter(
    (s) =>
      s.title.toLowerCase().includes(search.toLowerCase()) ||
      s.dataset_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Header
        title="Analysis History & Sessions"
        description="Search past conversational investigations, resume analyses, and inspect historical evidence."
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Search bar */}
        <div className="relative max-w-md">
          <Search className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search previous queries or datasets..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-card border border-border rounded-xl pl-9 pr-4 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary"
          />
        </div>

        {/* Sessions list */}
        {filteredSessions.length === 0 ? (
          <div className="p-12 text-center bg-card border border-dashed border-border rounded-xl text-xs text-muted-foreground">
            No analysis sessions match your search.
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {filteredSessions.map((s) => (
              <div
                key={s.id}
                className="bg-card border border-border rounded-xl p-5 shadow-sm hover:border-primary/50 transition-all flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                      {s.dataset_name}
                    </span>
                    <span className="text-[11px] text-muted-foreground flex items-center gap-1 font-mono">
                      <Calendar className="h-3 w-3" />
                      {formatDate(s.updated_at)}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors mb-1">
                    {s.title}
                  </h3>
                  <span className="text-[10px] text-muted-foreground font-mono">ID: {s.id}</span>
                </div>

                <div className="mt-4 pt-3 border-t border-border flex items-center justify-end">
                  <Link
                    href={`/analyst?session_id=${s.id}&dataset_id=${s.dataset_id}`}
                    className="inline-flex items-center gap-1 text-xs text-primary hover:text-primary/80 font-medium"
                  >
                    <span>Resume Workspace</span>
                    <ArrowRight className="h-3 w-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
