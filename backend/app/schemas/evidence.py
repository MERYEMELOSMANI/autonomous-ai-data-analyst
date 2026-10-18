from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class EvidenceRecord(BaseModel):
    id: str
    claim: str
    tool: Literal["duckdb_sql", "polars_agg", "statistical_test"]
    query_or_code: str
    columns_involved: List[str] = Field(default_factory=list)
    computed_values: Dict[str, Any] = Field(default_factory=dict)
    verification_status: Literal["VERIFIED", "FLAGGED", "REJECTED"]
    verification_diff: Optional[Dict[str, Any]] = None
    verification_notes: Optional[str] = None
    execution_time_ms: float = 0.0
    row_count: Optional[int] = None

class VerificationRequest(BaseModel):
    claim: str
    query_or_code: str
    expected_value: Any
    tolerance: float = 0.01

class VerificationResult(BaseModel):
    claim: str
    status: Literal["VERIFIED", "FLAGGED", "REJECTED"]
    actual_value: Any
    expected_value: Any
    discrepancy: Optional[float] = None
    is_supported: bool
    notes: str
    recomputation_ms: float
