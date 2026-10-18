export interface DatasetColumn {
  name: string;
  data_type: string;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  sample_values: any[];
  min_val?: number | string | null;
  max_val?: number | string | null;
  mean?: number | null;
  std_dev?: number | null;
  median?: number | null;
  q25?: number | null;
  q75?: number | null;
  outlier_count?: number;
}

export interface DataQualityReport {
  overall_score: number;
  total_rows: number;
  total_columns: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  total_missing_cells: number;
  missing_cells_percentage: number;
  warnings: Array<{
    severity: 'info' | 'warning' | 'critical';
    column?: string;
    message: string;
    suggestion?: string;
  }>;
}

export interface Dataset {
  id: string;
  name: string;
  filename: string;
  file_format: 'csv' | 'parquet' | 'xlsx' | 'xls';
  file_size: number;
  row_count: number;
  column_count: number;
  created_at: string;
  updated_at: string;
  columns: DatasetColumn[];
  quality_report?: DataQualityReport;
  sample_rows?: Record<string, any>[];
  duckdb_table_name?: string;
}

export interface EvidenceRecord {
  id: string;
  claim: string;
  tool: 'duckdb_sql' | 'polars_agg' | 'statistical_test';
  query_or_code: string;
  columns_involved: string[];
  computed_values: Record<string, any>;
  verification_status: 'VERIFIED' | 'FLAGGED' | 'REJECTED';
  verification_diff?: Record<string, any>;
  verification_notes?: string;
  execution_time_ms: number;
  row_count?: number;
}

export interface VisualizationSpec {
  id: string;
  title: string;
  chart_type: 'bar' | 'line' | 'scatter' | 'histogram' | 'box' | 'pie' | 'heatmap';
  description: string;
  plotly_figure: {
    data: any[];
    layout: Record<string, any>;
  };
  xAxis?: string;
  yAxis?: string;
}

export interface TimelineStep {
  id: string;
  agent: 'Supervisor' | 'Data Quality Agent' | 'Data Analysis Agent' | 'Visualization Agent' | 'Insight Verification Agent' | 'Report Agent';
  action: string;
  input_summary?: string;
  output_summary?: string;
  tool_name?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'retrying';
  duration_ms?: number;
  timestamp: string;
  details?: Record<string, any>;
}

export interface AnalysisMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  evidence?: EvidenceRecord[];
  visualizations?: VisualizationSpec[];
  timeline?: TimelineStep[];
  status?: 'thinking' | 'verifying' | 'completed' | 'error';
  workflow_id?: string;
}

export interface AnalysisSession {
  id: string;
  dataset_id: string;
  dataset_name: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: AnalysisMessage[];
}

export interface ReportItem {
  id: string;
  dataset_id: string;
  session_id?: string;
  title: string;
  objective: string;
  executive_summary: string;
  methodology: string;
  findings?: Array<{
    title: string;
    description: string;
    evidence_id?: string;
    verified: boolean;
    supporting_metrics?: Record<string, any>;
  }>;
  key_findings?: Array<{
    title: string;
    description: string;
    evidence_id?: string;
    verified: boolean;
  }>;
  visualizations: VisualizationSpec[];
  limitations: string[];
  conclusions: string[];
  created_at: string;
}
