from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.dataset_service import dataset_service
from app.schemas.dataset import DatasetResponse, SafeQueryRequest, SafeQueryResponse
from app.tools.duckdb_tool import duckdb_tool
from app.tools.polars_tool import polars_tool
from app.core.config import settings

router = APIRouter()

@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Upload a dataset (CSV, Parquet, or Excel), profile it, and register views."""
    try:
        dataset = await dataset_service.save_uploaded_dataset(file, db, name=name)
        # Fetch sample rows
        file_path = settings.UPLOAD_DIR / dataset.filename
        _, _, sample_rows = polars_tool.profile_dataset(file_path, dataset.file_format)
        
        resp = DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            filename=dataset.filename,
            file_format=dataset.file_format,
            file_size=dataset.file_size,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            duckdb_table_name=dataset.duckdb_table_name,
            columns=dataset.columns_json or [],
            quality_report=dataset.quality_report_json or None,
            sample_rows=sample_rows,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )
        return resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dataset: {str(e)}")

@router.get("", response_model=List[DatasetResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    """Retrieve all uploaded datasets."""
    datasets = await dataset_service.list_datasets(db)
    results = []
    for d in datasets:
        results.append(DatasetResponse(
            id=d.id,
            name=d.name,
            filename=d.filename,
            file_format=d.file_format,
            file_size=d.file_size,
            row_count=d.row_count,
            column_count=d.column_count,
            duckdb_table_name=d.duckdb_table_name,
            columns=d.columns_json or [],
            quality_report=d.quality_report_json or None,
            sample_rows=None,
            created_at=d.created_at,
            updated_at=d.updated_at
        ))
    return results

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Get metadata, columns, and quality report for a specific dataset."""
    dataset = await dataset_service.get_dataset_by_id(dataset_id, db)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    file_path = settings.UPLOAD_DIR / dataset.filename
    sample_rows = None
    if file_path.exists():
        try:
            _, _, sample_rows = polars_tool.profile_dataset(file_path, dataset.file_format)
        except Exception:
            pass

    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        filename=dataset.filename,
        file_format=dataset.file_format,
        file_size=dataset.file_size,
        row_count=dataset.row_count,
        column_count=dataset.column_count,
        duckdb_table_name=dataset.duckdb_table_name,
        columns=dataset.columns_json or [],
        quality_report=dataset.quality_report_json or None,
        sample_rows=sample_rows,
        created_at=dataset.created_at,
        updated_at=dataset.updated_at
    )

@router.get("/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: str,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated tabular rows for TanStack Table."""
    dataset = await dataset_service.get_dataset_by_id(dataset_id, db)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset_service.ensure_duckdb_registered(dataset)
    sql = f'SELECT * FROM "{dataset.duckdb_table_name}" LIMIT {limit} OFFSET {offset}'
    try:
        rows, cols, elapsed_ms = duckdb_tool.execute_safe_query(
            sql,
            allowed_table=dataset.duckdb_table_name,
            limit=limit
        )
        return {
            "columns": cols,
            "rows": rows,
            "total_rows": dataset.row_count,
            "limit": limit,
            "offset": offset,
            "execution_time_ms": elapsed_ms
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{dataset_id}/query", response_model=SafeQueryResponse)
async def execute_adhoc_query(
    dataset_id: str,
    req: SafeQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a safe ad-hoc read-only SQL query on the dataset table."""
    dataset = await dataset_service.get_dataset_by_id(dataset_id, db)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset_service.ensure_duckdb_registered(dataset)
    try:
        rows, cols, elapsed_ms = duckdb_tool.execute_safe_query(
            req.query,
            allowed_table=dataset.duckdb_table_name,
            limit=req.limit or 500
        )
        return SafeQueryResponse(
            columns=cols,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=elapsed_ms,
            query=req.query
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{dataset_id}/correlations")
async def get_correlations(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Compute Pearson correlation matrix of numeric columns."""
    dataset = await dataset_service.get_dataset_by_id(dataset_id, db)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    file_path = settings.UPLOAD_DIR / dataset.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Underlying file not found")

    try:
        corr_data = polars_tool.compute_correlations(file_path, dataset.file_format)
        return corr_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    """Delete dataset."""
    success = await dataset_service.delete_dataset(dataset_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": "Dataset deleted successfully"}
