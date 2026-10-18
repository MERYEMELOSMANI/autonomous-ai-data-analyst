'use client';

import React, { useState, useRef } from 'react';
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { uploadDatasetFile } from '@/lib/api';
import { formatBytes } from '@/lib/utils';
import { Dataset } from '@/lib/types';

interface DatasetUploaderProps {
  onSuccess: (dataset: Dataset) => void;
}

export function DatasetUploader({ onSuccess }: DatasetUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setError(null);
    setUploadSuccess(null);
    setIsUploading(true);
    try {
      const dataset = await uploadDatasetFile(file);
      setUploadSuccess(`Successfully ingested "${dataset.name}" with ${dataset.row_count.toLocaleString()} rows!`);
      onSuccess(dataset);
    } catch (err: any) {
      setError(err.message || 'Failed to upload dataset');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-150 flex flex-col items-center justify-center ${
          isDragging
            ? 'border-primary bg-primary/10 scale-[0.99]'
            : 'border-border bg-card/60 hover:bg-card/90 hover:border-border/80'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.parquet,.xlsx,.xls"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        <div className="h-12 w-12 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mb-3 shadow-inner">
          <UploadCloud className="h-6 w-6" />
        </div>

        <h3 className="font-semibold text-foreground text-sm tracking-tight mb-1">
          {isUploading ? 'Validating and Profiling Dataset...' : 'Click to upload or drag & drop'}
        </h3>
        <p className="text-xs text-muted-foreground max-w-sm">
          Supports CSV, Parquet, and Excel (.xlsx) files up to 100 MB. Instant DuckDB AST indexation & Polars profiling.
        </p>

        {isUploading && (
          <div className="mt-4 flex items-center gap-2 text-xs text-primary font-medium">
            <span className="h-2 w-2 rounded-full bg-primary animate-ping" />
            <span>Analyzing column distributions, duplicates & outliers...</span>
          </div>
        )}
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-3 bg-destructive/10 border border-destructive/20 text-rose-300 rounded-lg text-xs flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {uploadSuccess && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-lg text-xs flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{uploadSuccess}</span>
        </div>
      )}
    </div>
  );
}
