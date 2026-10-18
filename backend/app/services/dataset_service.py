import re
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import sanitize_filename, validate_file_extension
from app.database.models import DatasetModel
from app.schemas.dataset import DatasetResponse, DataQualitySummary, ColumnSummary
from app.tools.polars_tool import polars_tool
from app.tools.duckdb_tool import duckdb_tool

class DatasetService:
    @staticmethod
    def _create_clean_table_name(original_filename: str, dataset_id: str) -> str:
        """Create a safe SQL identifier for DuckDB table name."""
        stem = Path(original_filename).stem.lower()
        cleaned = re.sub(r'[^a-z0-9_]', '_', stem)[:20].strip('_')
        if not cleaned or not cleaned[0].isalpha():
            cleaned = f"t_{cleaned}"
        short_id = dataset_id.replace("-", "")[:8]
        return f"{cleaned}_{short_id}"

    @classmethod
    async def save_uploaded_dataset(
        cls,
        file: UploadFile,
        db: AsyncSession,
        name: Optional[str] = None
    ) -> DatasetModel:
        """Save an uploaded CSV, Excel, or Parquet dataset, profile it, and register in DuckDB."""
        if not validate_file_extension(file.filename or ""):
            raise ValueError(f"File extension not permitted. Allowed: {settings.ALLOWED_EXTENSIONS}")

        dataset_id = str(uuid.uuid4())
        safe_name = sanitize_filename(file.filename or "dataset")
        ext = Path(safe_name).suffix.lower().lstrip(".")
        
        target_filename = f"{dataset_id}_{safe_name}"
        target_path = settings.UPLOAD_DIR / target_filename

        # Stream copy and check size
        size = 0
        with open(target_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                size += len(chunk)
                if size > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Clean up
                    target_path.unlink(missing_ok=True)
                    raise ValueError(f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB")
                buffer.write(chunk)

        # Profile dataset using Polars
        try:
            columns_summary, quality_report, sample_rows = polars_tool.profile_dataset(target_path, ext)
        except Exception as e:
            target_path.unlink(missing_ok=True)
            raise ValueError(f"Failed to parse and profile dataset: {str(e)}")

        # Register in DuckDB
        table_name = cls._create_clean_table_name(safe_name, dataset_id)
        try:
            duckdb_tool.register_dataset(table_name, target_path, ext)
        except Exception as e:
            target_path.unlink(missing_ok=True)
            raise ValueError(f"Failed to register dataset view in DuckDB: {str(e)}")

        dataset_record = DatasetModel(
            id=dataset_id,
            name=name or Path(safe_name).stem.replace("_", " ").title(),
            filename=target_filename,
            file_format=ext,
            file_size=size,
            row_count=quality_report.total_rows,
            column_count=quality_report.total_columns,
            duckdb_table_name=table_name,
            columns_json=[col.model_dump() for col in columns_summary],
            quality_report_json=quality_report.model_dump(),
        )

        db.add(dataset_record)
        await db.commit()
        await db.refresh(dataset_record)
        return dataset_record

    @classmethod
    async def get_dataset_by_id(cls, dataset_id: str, db: AsyncSession) -> Optional[DatasetModel]:
        """Fetch dataset record by ID."""
        result = await db.execute(select(DatasetModel).where(DatasetModel.id == dataset_id))
        return result.scalars().first()

    @classmethod
    async def list_datasets(cls, db: AsyncSession) -> List[DatasetModel]:
        """Fetch all datasets ordered by upload date descending."""
        result = await db.execute(select(DatasetModel).order_by(DatasetModel.created_at.desc()))
        return list(result.scalars().all())

    @classmethod
    async def delete_dataset(cls, dataset_id: str, db: AsyncSession) -> bool:
        """Delete dataset file and database record."""
        dataset = await cls.get_dataset_by_id(dataset_id, db)
        if not dataset:
            return False

        # Remove physical file
        file_path = settings.UPLOAD_DIR / dataset.filename
        file_path.unlink(missing_ok=True)

        await db.delete(dataset)
        await db.commit()
        return True

    @classmethod
    def ensure_duckdb_registered(cls, dataset: DatasetModel) -> None:
        """Ensure the dataset's view is registered in the current DuckDB session."""
        file_path = settings.UPLOAD_DIR / dataset.filename
        if file_path.exists():
            duckdb_tool.register_dataset(dataset.duckdb_table_name, file_path, dataset.file_format)

dataset_service = DatasetService()
