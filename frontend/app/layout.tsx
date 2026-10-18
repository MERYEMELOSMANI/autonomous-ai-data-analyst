import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/sidebar';

export const metadata: Metadata = {
  title: 'Autonomous AI Data Analyst',
  description: 'Multi-agent autonomous analytics system with verifiable insights, DuckDB, Polars, and LangGraph.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground antialiased min-h-screen flex">
        <Sidebar />
        <main className="flex-1 flex flex-col h-screen overflow-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
