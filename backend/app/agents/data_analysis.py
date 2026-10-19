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
            findings = cls._extract_preliminary_findings(rows, col_names, query, schema_info, state.get("dataset_name", "Dataset"))

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
    def _is_id_col(name: str) -> bool:
        nl = name.lower().replace(" ", "_")
        return any(k in nl for k in ["id", "code", "ref", "key", "num", "no", "uuid", "identifier"])

    @classmethod
    def _find_label_col(cls, cols: List[str]) -> Optional[str]:
        for c in cols:
            if cls._is_id_col(c):
                continue
            nl = c.lower()
            if any(k in nl for k in ["nom", "name", "title", "titre", "label", "product", "produit", "item"]):
                return c
        return None

    @classmethod
    def _generate_heuristic_query(cls, query: str, table_name: str, schema_info: List[Dict[str, Any]]) -> tuple[str, str]:
        """Generate smart heuristic SQL query based on question keywords and column types."""
        q_lower = query.lower()

        numeric_cols = [
            c.get("name", c.get("column_name", ""))
            for c in schema_info
            if any(t in str(c.get("data_type", c.get("column_type", ""))).lower() for t in ["int", "float", "double", "decimal", "numeric", "real"])
        ]
        all_cat_cols = [
            c.get("name", c.get("column_name", ""))
            for c in schema_info
            if not any(t in str(c.get("data_type", c.get("column_type", ""))).lower() for t in ["int", "float", "double", "decimal", "numeric", "real"])
        ]

        label_col = cls._find_label_col(all_cat_cols)
        true_cat_cols = [c for c in all_cat_cols if not cls._is_id_col(c) and c != label_col]

        is_overview = any(phrase in q_lower for phrase in [
            "what is this data about", "what is this dataset", "what is this", "what is in", "tell me about",
            "overview", "describe", "explain", "summary", "summarize", "about", "what do we have", "what is this table",
            "what does this contain", "what do you understand", "c'est quoi", "de quoi", "données", "aperçu", "resume", "résumé"
        ])

        def clean_alias(col_name: str) -> str:
            cleaned = col_name.replace(" ", "_").replace("(", "").replace(")", "").replace("%", "pct").replace("€", "eur").replace("/", "_").replace("-", "_")
            return "".join(ch for ch in cleaned if ch.isalnum() or ch == "_")

        # Overview questions
        if is_overview:
            if numeric_cols:
                metrics_parts = ["COUNT(*) as total_records"]
                for num in numeric_cols[:2]:
                    ca = clean_alias(num)
                    metrics_parts.extend([
                        f'ROUND(AVG("{num}"), 2) as "avg_{ca}"',
                        f'ROUND(MIN("{num}"), 2) as "min_{ca}"',
                        f'ROUND(MAX("{num}"), 2) as "max_{ca}"'
                    ])
                sql = f'SELECT {", ".join(metrics_parts)} FROM "{table_name}"'
                return sql, "Aggregating dataset dimensions and baseline statistical distributions"
            return f'SELECT COUNT(*) as total_records FROM "{table_name}"', "Calculating total records"

        # Group-by query on genuine categories (never on raw IDs)
        if true_cat_cols and numeric_cols and any(k in q_lower for k in ["by", "category", "compare", "breakdown", "distribution", "group", "par", "selon", "répartition"]):
            cat = true_cat_cols[0]
            num = numeric_cols[0]
            ca = clean_alias(num)
            sql = f'SELECT "{cat}", COUNT(*) as record_count, ROUND(SUM("{num}"), 2) as "total_{ca}", ROUND(AVG("{num}"), 2) as "avg_{ca}" FROM "{table_name}" WHERE "{cat}" IS NOT NULL GROUP BY "{cat}" ORDER BY "total_{ca}" DESC LIMIT 15'
            return sql, f"Aggregating '{num}' grouped by '{cat}'"

        # Statistical summary query
        if numeric_cols and any(k in q_lower for k in ["average", "mean", "total", "sum", "stats", "summary", "pattern", "moyenne", "somme"]):
            num = numeric_cols[0]
            ca1 = clean_alias(num)
            num2 = numeric_cols[1] if len(numeric_cols) > 1 else None
            if num2:
                ca2 = clean_alias(num2)
                sql = f'SELECT COUNT(*) as total_records, ROUND(AVG("{num}"), 2) as "avg_{ca1}", ROUND(MIN("{num}"), 2) as "min_{ca1}", ROUND(MAX("{num}"), 2) as "max_{ca1}", ROUND(AVG("{num2}"), 2) as "avg_{ca2}" FROM "{table_name}"'
            else:
                sql = f'SELECT COUNT(*) as total_records, ROUND(AVG("{num}"), 2) as "avg_{ca1}", ROUND(MIN("{num}"), 2) as "min_{ca1}", ROUND(MAX("{num}"), 2) as "max_{ca1}" FROM "{table_name}"'
            return sql, "Calculating key summary statistics for numerical metrics"

        # Ranking / Top / Lowest items (multilingual)
        is_top = any(k in q_lower for k in [
            "top", "highest", "best", "max", "most", "cher", "chers", "chère", "chères", "plus grand", "élevé",
            "lowest", "bottom", "least", "cheapest", "min", "moins cher"
        ])
        if numeric_cols and is_top:
            order_dir = "ASC" if any(k in q_lower for k in ["lowest", "bottom", "least", "cheapest", "min", "moins"]) else "DESC"
            num = numeric_cols[0]
            if label_col:
                sql = f'SELECT "{label_col}", "{num}" FROM "{table_name}" WHERE "{label_col}" IS NOT NULL ORDER BY "{num}" {order_dir} LIMIT 10'
                return sql, f"Ranking top items by '{label_col}' according to '{num}' ({order_dir})"
            elif true_cat_cols:
                cat = true_cat_cols[0]
                ca = clean_alias(num)
                sql = f'SELECT "{cat}", ROUND(SUM("{num}"), 2) as "total_{ca}" FROM "{table_name}" WHERE "{cat}" IS NOT NULL GROUP BY "{cat}" ORDER BY "total_{ca}" {order_dir} LIMIT 10'
                return sql, f"Ranking categories by '{cat}' according to '{num}' ({order_dir})"

        # Default overview preview
        cols_to_select = [f'"{c}"' for c in (all_cat_cols[:3] + numeric_cols[:3]) if c]
        select_clause = ", ".join(cols_to_select) if cols_to_select else "*"
        sql = f'SELECT {select_clause} FROM "{table_name}" LIMIT 25'
        return sql, "Querying representative dataset records for analysis"

    @classmethod
    def _extract_preliminary_findings(cls, rows: List[Dict[str, Any]], col_names: List[str], query: str, schema_info: List[Dict[str, Any]] = None, dataset_name: str = "Dataset") -> List[Dict[str, Any]]:
        """Extract structured quantitative findings from result rows."""
        findings = []
        if not rows:
            return findings

        q_lower = query.lower()
        is_overview = any(phrase in q_lower for phrase in [
            "what is this data about", "what is this dataset", "what is this", "what is in", "tell me about",
            "overview", "describe", "explain", "summary", "summarize", "about", "what do we have",
            "what does this contain", "what do you understand"
        ])

        # If overview question
        if is_overview and len(rows) == 1:
            row = rows[0]
            total_items = row.get("total_records", row.get("total_items", len(rows)))
            cols_list = [c.get("name", c.get("column_name", "")) for c in (schema_info or [])]
            col_preview = ", ".join(cols_list[:5]) if cols_list else "tracked properties"
            
            findings.append({
                "title": f"Dataset Identity: {dataset_name}",
                "description": f"This dataset contains {total_items} records cataloging information across {len(schema_info or col_names)} attributes ({col_preview}).",
                "supporting_metrics": {"total_records": total_items}
            })

            # Check if average/min/max was computed
            for k, val in row.items():
                if k.startswith("avg_") and isinstance(val, (int, float)):
                    base_metric = k.replace("avg_", "")
                    min_val = row.get(f"min_{base_metric}")
                    max_val = row.get(f"max_{base_metric}")
                    findings.append({
                        "title": f"Key Metric Profile: {base_metric}",
                        "description": f"Across all records, '{base_metric}' averages {val:,.2f} ranging from {min_val} to {max_val}.",
                        "supporting_metrics": {f"avg_{base_metric}": val}
                    })
            return findings

        # If aggregated group by or ranked items
        if len(rows) > 1 and len(col_names) >= 2:
            first_row = rows[0]
            cat_col = col_names[0]
            val_col = col_names[-1]
            top_category = first_row.get(cat_col)
            top_val = first_row.get(val_col)
            formatted_top_val = f"{top_val:,.2f}" if isinstance(top_val, float) else f"{top_val:,}" if isinstance(top_val, int) else str(top_val)
            is_item = any(k in cat_col.lower() for k in ["nom", "name", "produit", "product", "item", "title", "record", "label"])
            top_title = f"Leading Item: {top_category}" if is_item else f"Top Performing Category: {top_category}"
            findings.append({
                "title": top_title,
                "description": f"The leading record '{top_category}' achieved {val_col} of {formatted_top_val}.",
                "supporting_metrics": {cat_col: top_category, val_col: top_val}
            })

            if len(rows) >= 3:
                second_row = rows[1]
                second_val = second_row.get(val_col)
                formatted_second_val = f"{second_val:,.2f}" if isinstance(second_val, float) else f"{second_val:,}" if isinstance(second_val, int) else str(second_val)
                second_title = f"Second Rank Item: {second_row.get(cat_col)}" if is_item else f"Second Rank Category: {second_row.get(cat_col)}"
                findings.append({
                    "title": second_title,
                    "description": f"The runner-up record '{second_row.get(cat_col)}' recorded {val_col} of {formatted_second_val} across {len(rows)} compared entries.",
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
