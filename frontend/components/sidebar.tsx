'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Database,
  BrainCircuit,
  GitMerge,
  BarChart3,
  FileText,
  History,
  Settings,
  Sparkles,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/datasets', label: 'Datasets', icon: Database },
  { href: '/analyst', label: 'AI Analyst', icon: BrainCircuit, badge: 'Multi-Agent' },
  { href: '/workflows', label: 'Agent Workflows', icon: GitMerge },
  { href: '/visualizations', label: 'Visualizations', icon: BarChart3 },
  { href: '/reports', label: 'Reports', icon: FileText },
  { href: '/history', label: 'Analysis History', icon: History },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-sidebar-border bg-sidebar flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-6 border-b border-sidebar-border gap-3">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <h1 className="font-semibold text-sm tracking-tight text-foreground">DataAnalyst AI</h1>
          <span className="text-[10px] text-muted-foreground font-mono">Autonomous Multi-Agent</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group',
                isActive
                  ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/25'
                  : 'text-sidebar-foreground hover:bg-secondary/60 hover:text-foreground'
              )}
            >
              <Icon className={cn('h-4 w-4 shrink-0 transition-transform group-hover:scale-105', isActive ? 'text-primary-foreground' : 'text-muted-foreground')} />
              <span className="truncate flex-1">{item.label}</span>
              {item.badge && (
                <span
                  className={cn(
                    'text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase tracking-wider',
                    isActive ? 'bg-primary-foreground/20 text-primary-foreground' : 'bg-primary/20 text-blue-400'
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* System Status Footer */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="bg-secondary/40 border border-border/40 rounded-lg p-3 flex items-center gap-2.5">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          <div className="text-xs">
            <div className="font-medium text-foreground flex items-center gap-1.5">
              <span>DuckDB & Polars</span>
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            </div>
            <span className="text-[11px] text-muted-foreground">Deterministic Guardrails</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
