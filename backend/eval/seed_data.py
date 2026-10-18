import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.session import AsyncSessionLocal, init_db
from app.database.models import DatasetModel, AnalysisSessionModel, AnalysisMessageModel, ReportModel, WorkflowRunModel
from app.tools.polars_tool import polars_tool
from app.tools.duckdb_tool import duckdb_tool
from app.core.config import settings

async def seed():
    print("Initializing database and seeding benchmark datasets...")
    await init_db()

    data_dir = Path(__file__).resolve().parent / "benchmarks"
    sample_files = [
        ("sales_performance.csv", "Sales Performance (2025)", "t_sales_2025"),
        ("customer_churn.csv", "Customer Retention & Churn", "t_churn_2025"),
        ("financial_transactions.csv", "Financial Transactions Audit", "t_fin_2025"),
    ]

    async with AsyncSessionLocal() as db:
        for filename, name, tbl in sample_files:
            filepath = data_dir / filename
            if not filepath.exists():
                print(f"File {filepath} not found, skipping.")
                continue

            # Copy to upload directory
            dest_file = settings.UPLOAD_DIR / f"seed_{filename}"
            with open(filepath, "rb") as src, open(dest_file, "wb") as dst:
                dst.write(src.read())

            ext = filepath.suffix.lstrip(".").lower()
            cols, quality, sample_rows = polars_tool.profile_dataset(dest_file, ext)

            # Register in DuckDB
            duckdb_tool.register_dataset(tbl, dest_file, ext)

            dataset_id = f"ds_{tbl}"
            # Check if exists
            from sqlalchemy.future import select
            existing = (await db.execute(select(DatasetModel).where(DatasetModel.id == dataset_id))).scalars().first()
            if not existing:
                record = DatasetModel(
                    id=dataset_id,
                    name=name,
                    filename=f"seed_{filename}",
                    file_format=ext,
                    file_size=filepath.stat().st_size,
                    row_count=quality.total_rows,
                    column_count=quality.total_columns,
                    duckdb_table_name=tbl,
                    columns_json=[c.model_dump() for c in cols],
                    quality_report_json=quality.model_dump(),
                )
                db.add(record)
                print(f"Created Dataset: {name} ({quality.total_rows} rows, table: {tbl})")

        await db.commit()
    print("Seed complete! All sample datasets are indexed and ready.")

if __name__ == "__main__":
    asyncio.run(seed())
