import pytest
from pathlib import Path
from app.tools.duckdb_tool import duckdb_tool
from app.tools.polars_tool import polars_tool

DATA_DIR = Path(__file__).resolve().parent.parent / "eval" / "benchmarks"

def test_polars_dataset_profiling():
    sales_file = DATA_DIR / "sales_performance.csv"
    assert sales_file.exists(), "sales_performance.csv must exist"

    cols, quality, sample_rows = polars_tool.profile_dataset(sales_file, "csv")
    
    # Assertions on profiling
    assert len(cols) == 8
    assert quality.total_rows == 1000
    assert quality.total_columns == 8
    assert quality.overall_score > 80.0
    assert len(sample_rows) == 100

    col_names = [c.name for c in cols]
    assert "sales_amount" in col_names
    assert "category" in col_names
    assert "region" in col_names

    # Check numeric stats
    sales_col = next(c for c in cols if c.name == "sales_amount")
    assert sales_col.mean is not None and sales_col.mean > 0
    assert sales_col.min_val is not None
    assert sales_col.max_val is not None

def test_duckdb_view_and_safe_query():
    sales_file = DATA_DIR / "sales_performance.csv"
    table_name = "test_sales_tbl"

    duckdb_tool.register_dataset(table_name, sales_file, "csv")
    
    # Safe query execution
    sql = f'SELECT "category", COUNT(*) as total_orders, ROUND(SUM("sales_amount"), 2) as revenue FROM "{table_name}" GROUP BY "category" ORDER BY revenue DESC'
    rows, cols, elapsed_ms = duckdb_tool.execute_safe_query(sql, allowed_table=table_name)
    
    assert len(rows) > 0
    assert "category" in cols
    assert "revenue" in cols
    assert elapsed_ms >= 0

    # Ensure forbidden query is caught
    with pytest.raises(ValueError):
        duckdb_tool.execute_safe_query(f'DROP VIEW "{table_name}"', allowed_table=table_name)

def test_correlation_matrix():
    sales_file = DATA_DIR / "sales_performance.csv"
    corr = polars_tool.compute_correlations(sales_file, "csv")
    assert "columns" in corr
    assert "matrix" in corr
    assert len(corr["columns"]) >= 3
