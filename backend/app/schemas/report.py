from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.analysis import VisualizationSpec

class FindingItem(BaseModel):
    title: str
    description: str
    evidence_id: Optional[str] = None
    verified: bool = True
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)

class ReportCreateRequest(BaseModel):
    dataset_id: str
    session_id: Optional[str] = None
    title: Optional[str] = None
    objective: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    dataset_id: str
    session_id: Optional[str] = None
    title: str
    objective: str
    executive_summary: str
    methodology: str
    findings: List[FindingItem] = Field(default_factory=list)
    visualizations: List[VisualizationSpec] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    conclusions: List[str] = Field(default_factory=list)
    created_at: datetime
