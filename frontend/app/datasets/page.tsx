'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Database,
  Trash2,
  Table,
  BarChart2,
  AlertTriangle,
  Layers,
  Sparkles,
  ArrowRight,
  Search,
  CheckCircle2,
  Terminal,
  Activity,
  PlusCircle,
} from 'lucide-react';
import { Header } from '@/components/header';
import { DatasetUploader } from '@/components/dataset-uploader';
import { DataTable } from '@/components/data-table';
import { fetchDatasets, fetchDatasetById, fetchDatasetPreview, deleteDataset, executeSafeQuery, fetchCorrelations } from '@/lib/api';
import { Dataset, DatasetColumn } from '@/lib/types';
import { formatBytes, formatDate } from '@/lib/utils';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [previewRows, setPreviewRows] = useState<Record<string, any>[]>([]);
  const [activeTab, setActiveTab] = useState<'preview' | 'schema' | 'quality' | 'query' | 'correlations'>('preview');
  const [adhocQuery, setAdhocQuery] = useState('');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [correlations, setCorrelations] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadAll = async () => {
    try {
      const data = await fetchDatasets();
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        selectDataset(data[0].id);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const selectDataset = async (id: string) => {
    try {
      const ds = await fetchDatasetById(id);
      setSelectedDataset(ds);
      setAdhocQuery(`SELECT * FROM "${ds.duckdb_table_name}" LIMIT 25;`);
      setQueryResult(null);
      setQueryError(null);

      // Fetch preview
      const prev = await fetchDatasetPreview(id, 50, 0);
      setPreviewRows(prev.rows || []);

      // Fetch correlations
      fetchCorrelations(id).then(setCorrelations).catch(() => setCorrelations(null));
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to permanently delete this dataset?')) return;
    try {
      await deleteDataset(id);
      setDatasets((prev) => prev.filter((d) => d.id !== id));
      if (selectedDataset?.id === id) {
        const remaining = datasets.filter((d) => d.id !== id);
        if (remaining.length > 0) {
          selectDataset(remaining[0].id);
        } else {
          setSelectedDataset(null);
          setPreviewRows([]);
        }
      }
    } catch (err) {
      alert('Failed to delete dataset');
    }
  };

  const handleRunQuery = async () => {
    if (!selectedDataset || !adhocQuery.trim()) return;
    setQueryError(null);
    try {
      const res = await executeSafeQuery(selectedDataset.id, adhocQuery, 100);
      setQueryResult(res);
    } catch (err: any) {
      setQueryError(err.message || 'Query execution rejected');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      <Header
        title="Dataset Management & Inspection Studio"
        description="Inspect schemas, column nullability, duplicate rows, IQR outliers, and DuckDB table views."
        actionButton={
          selectedDataset && (
            <Link
              href={`/analyst?dataset_id=${selectedDataset.id}`}
              className="flex items-center gap-2 px-3.5 py-1.5 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 shadow-sm transition-all"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Ask AI About This Data</span>
            </Link>
          )
        }
      />

      <div className="flex-1 overflow-y-auto p-8 space-y-6">
        {/* Upload Zone */}
        <DatasetUploader onSuccess={(newDs) => {
          setDatasets((prev) => [newDs, ...prev]);
          selectDataset(newDs.id);
        }} />

        {/* Dataset Selection Bar */}
        {datasets.length > 0 && (
          <div className="bg-card border border-border rounded-xl p-4 shadow-sm flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 overflow-x-auto py-1">
              {datasets.map((d) => (
                <button
                  key={d.id}
                  onClick={() => selectDataset(d.id)}
                  className={`px-3 py-2 rounded-lg text-xs font-medium shrink-0 flex items-center gap-2 transition-all ${
                    selectedDataset?.id === d.id
                      ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/20'
                      : 'bg-secondary/40 text-muted-foreground hover:bg-secondary/70 hover:text-foreground border border-border/50'
                  }`}
                >
                  <Database className="h-3.5 w-3.5" />
                  <span>{d.name}</span>
                  <span className="text-[10px] opacity-70">({d.row_count.toLocaleString()} rows)</span>
                </button>
              ))}
            </div>

            {selectedDataset && (
              <button
                onClick={() => handleDelete(selectedDataset.id)}
                className="p-2 rounded-lg text-muted-foreground hover:text-rose-400 hover:bg-rose-500/10 transition-colors shrink-0"
                title="Delete Dataset"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        )}

        {/* Selected Dataset Detail Panel */}
        {selectedDataset && (
          <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
            {/* Meta bar */}
            <div className="p-5 border-b border-border bg-secondary/20 flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-foreground text-sm">{selectedDataset.name}</h3>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                    View: {selectedDataset.duckdb_table_name}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground mt-1">
                  <span>Format: <strong>{selectedDataset.file_format.toUpperCase()}</strong></span>
                  <span>•</span>
                  <span>Size: <strong>{formatBytes(selectedDataset.file_size)}</strong></span>
                  <span>•</span>
                  <span>Rows: <strong>{selectedDataset.row_count.toLocaleString()}</strong></span>
                  <span>•</span>
                  <span>Columns: <strong>{selectedDataset.column_count}</strong></span>
                  <span>•</span>
                  <span>Uploaded: {formatDate(selectedDataset.created_at)}</span>
                </div>
              </div>

              {/* Quality Score Badge */}
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">Quality Score</div>
                  <div className="text-lg font-bold text-emerald-400">
                    {selectedDataset.quality_report?.overall_score || 100}/100
                  </div>
                </div>
              </div>
            </div>

            {/* Tab navigation */}
            <div className="px-5 border-b border-border flex items-center gap-6 text-xs font-medium">
              <button
                onClick={() => setActiveTab('preview')}
                className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === 'preview'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Table className="h-3.5 w-3.5" />
                <span>Table Preview</span>
              </button>

              <button
                onClick={() => setActiveTab('schema')}
                className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === 'schema'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                <span>Schema & Stats ({selectedDataset.columns.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('quality')}
                className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === 'quality'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>Quality Audit ({selectedDataset.quality_report?.warnings.length || 0})</span>
              </button>

              <button
                onClick={() => setActiveTab('correlations')}
                className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === 'correlations'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Activity className="h-3.5 w-3.5" />
                <span>Correlations</span>
              </button>

              <button
                onClick={() => setActiveTab('query')}
                className={`py-3.5 border-b-2 transition-colors flex items-center gap-2 ${
                  activeTab === 'query'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Terminal className="h-3.5 w-3.5" />
                <span>Safe SQL Query</span>
              </button>
            </div>

            {/* Tab Contents */}
            <div className="p-6">
              {/* Tab 1: Preview */}
              {activeTab === 'preview' && (
                <DataTable data={previewRows} pageSize={12} />
              )}

              {/* Tab 2: Schema & Stats */}
              {activeTab === 'schema' && (
                <div className="border border-border rounded-xl overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-secondary/40 border-b border-border text-[11px] font-semibold text-muted-foreground">
                      <tr>
                        <th className="py-2.5 px-4">Column</th>
                        <th className="py-2.5 px-4">Data Type</th>
                        <th className="py-2.5 px-4">Nulls (%)</th>
                        <th className="py-2.5 px-4">Unique</th>
                        <th className="py-2.5 px-4">Min / Max</th>
                        <th className="py-2.5 px-4">Mean (Std)</th>
                        <th className="py-2.5 px-4">Median (IQR Outliers)</th>
                        <th className="py-2.5 px-4">Sample Values</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {selectedDataset.columns.map((col) => (
                        <tr key={col.name} className="hover:bg-secondary/30 transition-colors">
                          <td className="py-2.5 px-4 font-semibold text-foreground font-mono">{col.name}</td>
                          <td className="py-2.5 px-4 font-mono text-muted-foreground">{col.data_type}</td>
                          <td className="py-2.5 px-4">
                            <span className={col.null_percentage > 20 ? 'text-amber-400 font-semibold' : 'text-muted-foreground'}>
                              {col.null_count} ({col.null_percentage}%)
                            </span>
                          </td>
                          <td className="py-2.5 px-4 font-mono text-foreground">{col.unique_count.toLocaleString()}</td>
                          <td className="py-2.5 px-4 font-mono text-muted-foreground">
                            {col.min_val !== null ? `${col.min_val} / ${col.max_val}` : '—'}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-muted-foreground">
                            {col.mean !== null ? `${col.mean} (±${col.std_dev})` : '—'}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-muted-foreground">
                            {col.median !== null ? (
                              <span>
                                {col.median}{' '}
                                {col.outlier_count ? (
                                  <span className="text-amber-400 font-semibold">({col.outlier_count} IQR)</span>
                                ) : (
                                  '(0)'
                                )}
                              </span>
                            ) : (
                              '—'
                            )}
                          </td>
                          <td className="py-2.5 px-4 font-mono text-[11px] text-blue-300 truncate max-w-[200px]">
                            {col.sample_values ? col.sample_values.slice(0, 3).join(', ') : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Tab 3: Quality Audit */}
              {activeTab === 'quality' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-secondary/30 p-4 rounded-xl border border-border">
                      <div className="text-xs text-muted-foreground mb-1">Duplicate Records</div>
                      <div className="text-xl font-bold text-foreground">
                        {selectedDataset.quality_report?.duplicate_rows.toLocaleString()}
                        <span className="text-xs font-normal text-muted-foreground ml-1.5">
                          ({selectedDataset.quality_report?.duplicate_percentage}%)
                        </span>
                      </div>
                    </div>
                    <div className="bg-secondary/30 p-4 rounded-xl border border-border">
                      <div className="text-xs text-muted-foreground mb-1">Missing Cells</div>
                      <div className="text-xl font-bold text-foreground">
                        {selectedDataset.quality_report?.total_missing_cells.toLocaleString()}
                        <span className="text-xs font-normal text-muted-foreground ml-1.5">
                          ({selectedDataset.quality_report?.missing_cells_percentage}%)
                        </span>
                      </div>
                    </div>
                    <div className="bg-secondary/30 p-4 rounded-xl border border-border">
                      <div className="text-xs text-muted-foreground mb-1">Health Score</div>
                      <div className="text-xl font-bold text-emerald-400">
                        {selectedDataset.quality_report?.overall_score || 100} / 100
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 mt-4">
                    <h4 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                      Auditor Warnings & Suggestions
                    </h4>
                    {(!selectedDataset.quality_report?.warnings || selectedDataset.quality_report.warnings.length === 0) ? (
                      <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-lg text-xs flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>No critical anomalies or missing data issues detected. Dataset is clean!</span>
                      </div>
                    ) : (
                      selectedDataset.quality_report.warnings.map((w, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-secondary/30 border border-border/80 rounded-lg text-xs space-y-1"
                        >
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[10px] uppercase font-mono px-1.5 py-0.5 rounded font-semibold ${
                                w.severity === 'critical'
                                  ? 'bg-rose-500/20 text-rose-300'
                                  : w.severity === 'warning'
                                  ? 'bg-amber-500/20 text-amber-300'
                                  : 'bg-blue-500/20 text-blue-300'
                              }`}
                            >
                              {w.severity}
                            </span>
                            {w.column && <span className="font-mono text-foreground font-semibold">Column '{w.column}'</span>}
                          </div>
                          <p className="text-muted-foreground">{w.message}</p>
                          {w.suggestion && (
                            <p className="text-[11px] text-blue-300/80 italic">💡 {w.suggestion}</p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Tab 4: Correlations */}
              {activeTab === 'correlations' && (
                <div>
                  {correlations && correlations.matrix && correlations.matrix.length > 0 ? (
                    <div className="border border-border rounded-xl overflow-x-auto">
                      <table className="w-full text-center text-xs">
                        <thead className="bg-secondary/40 border-b border-border">
                          <tr>
                            <th className="py-2.5 px-3 text-left font-semibold text-muted-foreground">Variable</th>
                            {correlations.columns.map((c: string) => (
                              <th key={c} className="py-2.5 px-3 font-mono font-medium text-muted-foreground">{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border/60">
                          {correlations.matrix.map((row: any, i: number) => {
                            const rowVar = correlations.columns[i];
                            return (
                              <tr key={i} className="hover:bg-secondary/30">
                                <td className="py-2.5 px-3 text-left font-semibold font-mono text-foreground">{rowVar}</td>
                                {correlations.columns.map((c: string) => {
                                  const val = row[c];
                                  const isPositive = val > 0.4;
                                  const isNegative = val < -0.4;
                                  return (
                                    <td
                                      key={c}
                                      className={`py-2.5 px-3 font-mono ${
                                        val === 1
                                          ? 'text-muted-foreground/50'
                                          : isPositive
                                          ? 'text-emerald-400 font-semibold bg-emerald-500/5'
                                          : isNegative
                                          ? 'text-rose-400 font-semibold bg-rose-500/5'
                                          : 'text-muted-foreground'
                                      }`}
                                    >
                                      {val !== undefined ? val.toFixed(3) : '—'}
                                    </td>
                                  );
                                })}
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground py-6 text-center">
                      Not enough numerical columns to calculate correlation matrix.
                    </p>
                  )}
                </div>
              )}

              {/* Tab 5: Safe Query */}
              {activeTab === 'query' && (
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block mb-1.5">
                      DuckDB Read-Only SQL Sandbox (AST Validated)
                    </label>
                    <textarea
                      rows={4}
                      value={adhocQuery}
                      onChange={(e) => setAdhocQuery(e.target.value)}
                      className="w-full bg-black/50 border border-border rounded-lg p-3 text-xs font-mono text-emerald-300 focus:outline-none focus:border-primary resize-y"
                    />
                  </div>

                  <button
                    onClick={handleRunQuery}
                    className="px-4 py-2 bg-primary text-primary-foreground text-xs font-medium rounded-lg hover:bg-primary/90 flex items-center gap-2"
                  >
                    <Terminal className="h-3.5 w-3.5" />
                    <span>Execute Safe Query</span>
                  </button>

                  {queryError && (
                    <div className="p-3 bg-destructive/10 border border-destructive/20 text-rose-300 text-xs rounded-lg flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                      <span>{queryError}</span>
                    </div>
                  )}

                  {queryResult && (
                    <div className="space-y-2 mt-4">
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>Returned {queryResult.row_count} rows in <strong>{queryResult.execution_time_ms} ms</strong></span>
                      </div>
                      <DataTable data={queryResult.rows} columns={queryResult.columns} pageSize={10} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
