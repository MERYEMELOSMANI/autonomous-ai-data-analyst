from typing import TypedDict, List, Dict, Any, Optional

class AnalystState(TypedDict, total=False):
    session_id: str
    workflow_id: str
    query: str
    dataset_id: str
    table_name: str
    dataset_name: str
    schema_info: List[Dict[str, Any]]
    sample_rows: List[Dict[str, Any]]
    quality_summary: Dict[str, Any]
    
    # Workflow coordination
    plan: List[str]
    current_agent: str
    timeline: List[Dict[str, Any]]
    retry_count: int
    needs_revision: bool
    revision_reason: Optional[str]
    status: str  # running, completed, failed
    error: Optional[str]
    
    # Analytical outputs
    data_quality_notes: List[str]
    sql_queries: List[Dict[str, Any]]
    query_results: List[Dict[str, Any]]
    evidence_records: List[Dict[str, Any]]
    visualizations: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    report_sections: Dict[str, Any]
    final_response: str
