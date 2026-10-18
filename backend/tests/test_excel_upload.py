import pytest
from pathlib import Path
import pandas as pd
from app.tools.duckdb_tool import duckdb_tool
from app.tools.polars_tool import polars_tool

def test_excel_registration_and_query(tmp_path):
    excel_path = tmp_path / "test_inventory.xlsx"
    df = pd.DataFrame({
        "product_name": ["Laptop", "Monitor", "Keyboard", "Mouse"],
        "category": ["Electronics", "Electronics", "Accessories", "Accessories"],
        "unit_price": [1200.0, 300.0, 75.0, 25.0],
        "stock_qty": [15, 40, 100, 250]
    })
    df.to_excel(excel_path, index=False)

    # 1. Profile with Polars
    cols, quality, sample_rows = polars_tool.profile_dataset(excel_path, "xlsx")
    assert len(cols) == 4
    assert quality.total_rows == 4
    assert quality.total_columns == 4

    # 2. Register in DuckDB
    table_name = "test_inventory_tbl"
    duckdb_tool.register_dataset(table_name, excel_path, "xlsx")

    # 3. Safe query execution
    sql = f'SELECT "category", SUM("stock_qty") as total_stock, ROUND(AVG("unit_price"), 2) as avg_price FROM "{table_name}" GROUP BY "category" ORDER BY total_stock DESC'
    rows, cols_out, elapsed_ms = duckdb_tool.execute_safe_query(sql, allowed_table=table_name)
    
    assert len(rows) == 2
    assert "category" in cols_out
    assert "total_stock" in cols_out
    assert rows[0]["category"] == "Accessories"
    assert rows[0]["total_stock"] == 350
