import time
import logging
from typing import Dict, Any, List, Optional
from app.agents.state import AnalystState
from app.agents.llm_client import llm_provider
from app.tools.duckdb_tool import duckdb_tool

logger = logging.getLogger(__name__)

class DataAnalysisAgent:
    @classmethod
    async def run(cls, state: AnalystState) -> Dict[str, Any]:
        """
        Data Analysis Agent:
        Translates user question into analytical SQL queries, executes them
        deterministically via DuckDB, computes aggregations, and extracts factual findings.
        """
        start_time = time.perf_counter()
        query = state.get("query", "")
        table_name = state.get("table_name", "dataset")
        schema_info = state.get("schema_info", [])
        
        # Prepare schema details
        columns = [c.get("name", c.get("column_name", "")) for c in schema_info]
        types = [c.get("data_type", c.get("column_type", "")) for c in schema_info]
        schema_str = ", ".join([f'"{c}" ({t})' for c, t in zip(columns, types) if c])

        # Generate SQL Query
        sql_query: Optional[str] = None
        analysis_rationale = ""

        if llm_provider.is_configured():
            prompt = f"""You are the Data Analysis Agent in an autonomous data analyst system.
User Question: "{query}"
Target DuckDB Table: "{table_name}"
Table Schema: {schema_str}

Generate a safe, read-only SQL query (DuckDB dialect) to calculate the precise numbers required to answer the question.
Rules:
1. ONLY SELECT statements are permitted.
2. Only query the table "{table_name}".
3. Always use double quotes around column names and table names to handle special characters or spaces.
4. Keep the query focused, clean, and bounded (use aggregations like SUM, AVG, COUNT, MIN, MAX).

Return JSON:
{{
  "sql": "SELECT ... FROM ...",
  "rationale": "Brief 1-sentence explanation of what is calculated"
}}
"""
            res = await llm_provider.generate_json(prompt)
            if res and "sql" in res and isinstance(res["sql"], str):
                sql_query = res["sql"].strip()
                analysis_rationale = res.get("rationale", "")

        # Fallback to intelligent deterministic heuristic query generator
        if not sql_query:
            sql_query, analysis_rationale = cls._generate_heuristic_query(query, table_name, schema_info)

        # Execute Query via DuckDB
        executed_queries = list(state.get("sql_queries", []))
        query_results = list(state.get("query_results", []))
        findings: List[Dict[str, Any]] = []
        error_msg = None

        try:
            rows, col_names, query_time_ms = duckdb_tool.execute_safe_query(
                sql_query,
                allowed_table=table_name,
                limit=100
            )

            executed_queries.append({
                "query": sql_query,
                "table": table_name,
                "execution_time_ms": query_time_ms,
                "row_count": len(rows),
                "rationale": analysis_rationale
            })

            query_results.append({
                "columns": col_names,
                "rows": rows,
                "row_count": len(rows)
            })

            # Derive preliminary findings from data rows
            findings = cls._extract_preliminary_findings(rows, col_names, query)

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Analysis query execution error: {error_msg}")
            # If failed, attempt safe fallback query
            try:
                fallback_sql = f'SELECT * FROM "{table_name}" LIMIT 20'
                rows, col_names, query_time_ms = duckdb_tool.execute_safe_query(fallback_sql, allowed_table=table_name, limit=20)
                executed_queries.append({
                    "query": fallback_sql,
                    "table": table_name,
                    "execution_time_ms": query_time_ms,
                    "row_count": len(rows),
                    "rationale": "Fallback overview query after syntax recovery"
                })
                query_results.append({
                    "columns": col_names,
                    "rows": rows,
                    "row_count": len(rows)
                })
                findings.append({
                    "title": "Dataset Preview",
                    "description": f"Retrieved top {len(rows)} sample records from {table_name}.",
                    "supporting_metrics": {"rows_retrieved": len(rows)}
                })
            except Exception as fe:
                error_msg = f"{error_msg} | Fallback failed: {fe}"

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        timeline_step = {
            "id": f"step_analysis_{int(time.time()*1000)}",
            "agent": "Data Analysis Agent",
            "action": "Generated and executed deterministic DuckDB queries",
            "input_summary": f"Query: {sql_query[:80]}...",
            "output_summary": f"Executed in {elapsed_ms}ms with {len(findings)} initial findings" if not error_msg else f"Query failed: {error_msg[:60]}",
            "tool_name": "duckdb_tool.execute_safe_query",
            "status": "completed" if not error_msg else "failed",
            "duration_ms": elapsed_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {
                "sql": sql_query,
                "rationale": analysis_rationale,
                "findings_count": len(findings),
                "error": error_msg
            }
        }

        current_timeline = list(state.get("timeline", []))
        current_timeline.append(timeline_step)

        return {
            "sql_queries": executed_queries,
            "query_results": query_results,
            "findings": findings,
            "current_agent": "Insight Verification Agent",
            "timeline": current_timeline,
        }

    @staticmethod
    def _generate_heuristic_query(query: str, table_name: str, schema_info: List[Dict[str, Any]]) -> tuple[str, str]:
        """Generate smart heuristic SQL query based on question keywords and column types."""
        numeric_cols = [
            c.get("name", c.get("column_name", ""))
            for c in schema_info
            if any(t in str(c.get("data_type", c.get("column_type", ""))).lower() for t in ["int", "float", "double", "decimal", "numeric", "real"])
        ]
        cat_cols = [
            c.get("name", c.get("column_name", ""))
            for c in schema_info
            if not any(t in str(c.get("data_type", c.get("column_type", ""))).lower() for t in ["int", "float", "double", "decimal", "numeric", "real"])
        ]

        q_lower = query.lower()

        # Group-by query
        if cat_cols and numeric_cols and any(k in q_lower for k in ["by", "category", "compare", "breakdown", "top", "distribution", "highest", "lowest", "most"]):
            cat = cat_cols[0]
            num = numeric_cols[0]
            sql = f'SELECT "{cat}", COUNT(*) as record_count, ROUND(SUM("{num}"), 2) as total_{num}, ROUND(AVG("{num}"), 2) as avg_{num} FROM "{table_name}" WHERE "{cat}" IS NOT NULL GROUP BY "{cat}" ORDER BY total_{num} DESC LIMIT 15'
            return sql, f"Aggregating '{num}' grouped by '{cat}'"

        # Statistical summary query
        if numeric_cols and any(k in q_lower for k in ["average", "mean", "total", "sum", "stats", "summary", "pattern"]):
            num = numeric_cols[0]
            num2 = numeric_cols[1] if len(numeric_cols) > 1 else None
            if num2:
                sql = f'SELECT COUNT(*) as total_records, ROUND(AVG("{num}"), 2) as avg_{num}, ROUND(MIN("{num}"), 2) as min_{num}, ROUND(MAX("{num}"), 2) as max_{num}, ROUND(AVG("{num2}"), 2) as avg_{num2} FROM "{table_name}"'
            else:
                sql = f'SELECT COUNT(*) as total_records, ROUND(AVG("{num}"), 2) as avg_{num}, ROUND(MIN("{num}"), 2) as min_{num}, ROUND(MAX("{num}"), 2) as max_{num} FROM "{table_name}"'
            return sql, f"Calculating key summary statistics for numerical metrics"

        # Default overview query
        cols_to_select = [f'"{c}"' for c in (cat_cols[:3] + numeric_cols[:3]) if c]
        select_clause = ", ".join(cols_to_select) if cols_to_select else "*"
        sql = f'SELECT {select_clause} FROM "{table_name}" LIMIT 25'
        return sql, "Querying representative dataset records for analysis"

    @staticmethod
    def _extract_preliminary_findings(rows: List[Dict[str, Any]], col_names: List[str], query: str) -> List[Dict[str, Any]]:
        """Extract structured quantitative findings from result rows."""
        findings = []
        if not rows:
            return findings

        # If aggregated group by
        if len(rows) > 1 and len(col_names) >= 2:
            first_row = rows[0]
            cat_col = col_names[0]
            val_col = col_names[-1]
            top_category = first_row.get(cat_col)
            top_val = first_row.get(val_col)
            formatted_top_val = f"{top_val:,.2f}" if isinstance(top_val, float) else f"{top_val:,}" if isinstance(top_val, int) else str(top_val)
            findings.append({
                "title": f"Top Performing Category: {top_category}",
                "description": f"The leading segment '{top_category}' achieved {val_col} of {formatted_top_val}.",
                "supporting_metrics": {cat_col: top_category, val_col: top_val}
            })

            if len(rows) >= 3:
                second_row = rows[1]
                second_val = second_row.get(val_col)
                formatted_second_val = f"{second_val:,.2f}" if isinstance(second_val, float) else f"{second_val:,}" if isinstance(second_val, int) else str(second_val)
                findings.append({
                    "title": f"Second Rank: {second_row.get(cat_col)}",
                    "description": f"The runner-up segment '{second_row.get(cat_col)}' recorded {val_col} of {formatted_second_val} across {len(rows)} compared categories.",
                    "supporting_metrics": {cat_col: second_row.get(cat_col), val_col: second_val}
                })

        elif len(rows) == 1:
            row = rows[0]
            for col, val in row.items():
                if isinstance(val, (int, float)):
                    formatted_val = f"{val:,.2f}" if isinstance(val, float) else f"{val:,}" if isinstance(val, int) else str(val)
                    findings.append({
                        "title": f"Calculated Metric: {col}",
                        "description": f"The computed {col} is {formatted_val}.",
                        "supporting_metrics": {col: val}
                    })

        return findings
