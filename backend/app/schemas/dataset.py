from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ColumnSummary(BaseModel):
    name: str
    data_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any] = Field(default_factory=list)
    min_val: Optional[Any] = None
    max_val: Optional[Any] = None
    mean: Optional[float] = None
    std_dev: Optional[float] = None
    median: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    outlier_count: Optional[int] = 0

class QualityWarning(BaseModel):
    severity: str  # 'info', 'warning', 'critical'
    column: Optional[str] = None
    message: str
    suggestion: Optional[str] = None

class DataQualitySummary(BaseModel):
    overall_score: float  # 0 to 100
    total_rows: int
    total_columns: int
    duplicate_rows: int
    duplicate_percentage: float
    total_missing_cells: int
    missing_cells_percentage: float
    warnings: List[QualityWarning] = Field(default_factory=list)

class DatasetBase(BaseModel):
    name: str
    filename: str
    file_format: str
    file_size: int
    row_count: int
    column_count: int
    duckdb_table_name: str

class DatasetResponse(DatasetBase):
    id: str
    columns: List[ColumnSummary] = Field(default_factory=list)
    quality_report: Optional[DataQualitySummary] = None
    sample_rows: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SafeQueryRequest(BaseModel):
    query: str
    limit: Optional[int] = 500

class SafeQueryResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    query: str
