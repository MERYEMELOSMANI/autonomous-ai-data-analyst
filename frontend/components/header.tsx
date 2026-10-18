'use client';

import React from 'react';
import Link from 'next/link';
import { Database, PlusCircle, CheckCircle2, ShieldAlert } from 'lucide-react';

interface HeaderProps {
  title: string;
  description?: string;
  datasetName?: string;
  actionButton?: React.ReactNode;
}

export function Header({ title, description, datasetName, actionButton }: HeaderProps) {
  return (
    <header className="h-16 border-b border-border bg-background/80 backdrop-blur px-8 flex items-center justify-between shrink-0">
      <div>
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-foreground tracking-tight">{title}</h2>
          {datasetName && (
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-medium text-blue-400">
              <Database className="h-3 w-3" />
              <span>{datasetName}</span>
            </div>
          )}
        </div>
        {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
      </div>

      <div className="flex items-center gap-3">
        {actionButton}
      </div>
    </header>
  );
}
