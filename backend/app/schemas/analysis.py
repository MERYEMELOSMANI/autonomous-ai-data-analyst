from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.evidence import EvidenceRecord

class VisualizationSpec(BaseModel):
    id: str
    title: str
    chart_type: Literal["bar", "line", "scatter", "histogram", "box", "pie", "heatmap"]
    description: str
    plotly_figure: Dict[str, Any]
    xAxis: Optional[str] = None
    yAxis: Optional[str] = None

class TimelineStepSchema(BaseModel):
    id: str
    agent: str
    action: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    tool_name: Optional[str] = None
    status: Literal["pending", "running", "completed", "failed", "retrying"]
    duration_ms: Optional[float] = None
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class AnalysisQueryRequest(BaseModel):
    dataset_id: str
    session_id: Optional[str] = None
    query: str
    focus_columns: Optional[List[str]] = None

class AnalysisMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    evidence: Optional[List[EvidenceRecord]] = None
    visualizations: Optional[List[VisualizationSpec]] = None
    timeline: Optional[List[TimelineStepSchema]] = None
    status: str
    workflow_id: Optional[str] = None
    created_at: datetime

class AnalysisSessionResponse(BaseModel):
    id: str
    dataset_id: str
    dataset_name: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[AnalysisMessageResponse] = Field(default_factory=list)
