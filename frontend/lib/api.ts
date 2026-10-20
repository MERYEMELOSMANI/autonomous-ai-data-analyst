import { Dataset, AnalysisSession, ReportItem, EvidenceRecord, VisualizationSpec } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001/api/v1';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchDatasets(): Promise<Dataset[]> {
  const res = await fetch(`${API_BASE}/datasets`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch datasets');
  return res.json();
}

export async function fetchDatasetById(id: string): Promise<Dataset> {
  const res = await fetch(`${API_BASE}/datasets/${id}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch dataset');
  return res.json();
}

export async function fetchDatasetPreview(id: string, limit = 50, offset = 0) {
  const res = await fetch(`${API_BASE}/datasets/${id}/preview?limit=${limit}&offset=${offset}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch preview');
  return res.json();
}

export async function fetchCorrelations(id: string) {
  const res = await fetch(`${API_BASE}/datasets/${id}/correlations`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch correlations');
  return res.json();
}

export async function uploadDatasetFile(file: File, name?: string): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);
  const url = name ? `${API_BASE}/datasets/upload?name=${encodeURIComponent(name)}` : `${API_BASE}/datasets/upload`;
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function deleteDataset(id: string) {
  const res = await fetch(`${API_BASE}/datasets/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete dataset');
  return res.json();
}

export async function executeSafeQuery(datasetId: string, query: string, limit = 100) {
  const res = await fetch(`${API_BASE}/datasets/${datasetId}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Query failed' }));
    throw new Error(err.detail || 'Query execution failed');
  }
  return res.json();
}

export async function fetchSessions(): Promise<AnalysisSession[]> {
  const res = await fetch(`${API_BASE}/analyst/sessions`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch sessions');
  return res.json();
}

export async function fetchSessionById(id: string): Promise<AnalysisSession> {
  const res = await fetch(`${API_BASE}/analyst/sessions/${id}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch session');
  return res.json();
}

export async function createSession(datasetId: string, title?: string): Promise<AnalysisSession> {
  const url = title
    ? `${API_BASE}/analyst/sessions?dataset_id=${datasetId}&title=${encodeURIComponent(title)}`
    : `${API_BASE}/analyst/sessions?dataset_id=${datasetId}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export function getStreamUrl(datasetId: string, query: string, sessionId?: string) {
  let url = `${API_BASE}/analyst/stream?dataset_id=${encodeURIComponent(datasetId)}&query=${encodeURIComponent(query)}`;
  if (sessionId) {
    url += `&session_id=${encodeURIComponent(sessionId)}`;
  }
  return url;
}

export async function fetchWorkflows() {
  const res = await fetch(`${API_BASE}/workflows`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch workflows');
  return res.json();
}

export async function fetchWorkflowDetails(id: string) {
  const res = await fetch(`${API_BASE}/workflows/${id}`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch workflow details');
  return res.json();
}

export async function fetchVisualizations(): Promise<VisualizationSpec[]> {
  const res = await fetch(`${API_BASE}/visualizations`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch visualizations');
  return res.json();
}

export async function fetchReports(): Promise<ReportItem[]> {
  const res = await fetch(`${API_BASE}/reports`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch reports');
  return res.json();
}

export async function createReport(datasetId: string, sessionId?: string, title?: string): Promise<ReportItem> {
  const res = await fetch(`${API_BASE}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dataset_id: datasetId, session_id: sessionId, title }),
  });
  if (!res.ok) throw new Error('Failed to create report');
  return res.json();
}

export function getReportHtmlUrl(id: string) {
  return `${API_BASE}/reports/${id}/html`;
}

export async function fetchSettings() {
  const res = await fetch(`${API_BASE}/settings`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Failed to fetch settings');
  return res.json();
}

export async function updateSettings(data: { gemini_api_key?: string; gemini_model?: string; observability_enabled?: boolean }) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update settings');
  return res.json();
}
