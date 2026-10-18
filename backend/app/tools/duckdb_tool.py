import time
import duckdb
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from app.core.config import settings
from app.core.security import validate_sql_query

class DuckDBTool:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(settings.DUCKDB_DIR / "analytics.duckdb")
        # DuckDB in-memory or file connection
        self.conn = duckdb.connect(self.db_path)
        # Configure thread count and memory limit for safety
        self.conn.execute("SET memory_limit = '2GB';")
        self.conn.execute("SET threads TO 4;")

    def register_dataset(self, table_name: str, file_path: Path, file_format: str) -> None:
        """Register a CSV or Parquet file as a DuckDB table/view."""
        path_str = str(file_path).replace("\\", "/")
        if file_format == "csv":
            self.conn.execute(
                f"CREATE OR REPLACE VIEW \"{table_name}\" AS SELECT * FROM read_csv_auto('{path_str}');"
            )
        elif file_format == "parquet":
            self.conn.execute(
                f"CREATE OR REPLACE VIEW \"{table_name}\" AS SELECT * FROM read_parquet('{path_str}');"
            )
        elif file_format in ["xlsx", "xls"]:
            # For excel, it's typically pre-converted to parquet or csv on upload
            self.conn.execute(
                f"CREATE OR REPLACE VIEW \"{table_name}\" AS SELECT * FROM read_parquet('{path_str}');"
            )
        else:
            raise ValueError(f"Unsupported file format for DuckDB: {file_format}")

    def execute_safe_query(
        self,
        query: str,
        allowed_table: Optional[str] = None,
        limit: int = 500
    ) -> Tuple[List[Dict[str, Any]], List[str], float]:
        """
        Validate and execute a strictly read-only SQL query.
        Returns: (rows as dicts, column names, execution_time_ms)
        """
        is_valid, error_msg = validate_sql_query(query, allowed_table=allowed_table)
        if not is_valid:
            raise ValueError(f"SQL validation failed: {error_msg}")

        # Ensure bounded limit
        final_query = query.strip().rstrip(";")
        if "LIMIT " not in final_query.upper():
            final_query = f"{final_query} LIMIT {limit}"

        start_time = time.perf_counter()
        cursor = self.conn.cursor()
        try:
            cursor.execute(final_query)
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            raw_rows = cursor.fetchall()
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            rows: List[Dict[str, Any]] = []
            for r in raw_rows:
                row_dict = {}
                for idx, col in enumerate(col_names):
                    val = r[idx]
                    # Handle non-JSON serializable types
                    if hasattr(val, "isoformat"):
                        val = val.isoformat()
                    row_dict[col] = val
                rows.append(row_dict)

            return rows, col_names, elapsed_ms
        finally:
            cursor.close()

    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """Retrieve column names and types for a registered table."""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"DESCRIBE \"{table_name}\"")
            results = cursor.fetchall()
            return [{"column_name": r[0], "column_type": r[1], "null": r[2]} for r in results]
        finally:
            cursor.close()

# Global singleton
duckdb_tool = DuckDBTool()
