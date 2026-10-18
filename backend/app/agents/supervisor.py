import time
from typing import Dict, Any, List
from app.agents.state import AnalystState
from app.agents.llm_client import llm_provider

class SupervisorAgent:
    @staticmethod
    async def run(state: AnalystState) -> Dict[str, Any]:
        """
        Supervisor Agent:
        Analyzes the user's inquiry, identifies dataset columns of interest,
        and generates an execution plan for the downstream agents.
        """
        start_time = time.perf_counter()
        query = state.get("query", "")
        table_name = state.get("table_name", "dataset")
        schema_info = state.get("schema_info", [])
        
        # Prepare schema representation for planning
        columns_desc = ", ".join([f"{col.get('column_name', col.get('name', ''))} ({col.get('column_type', col.get('data_type', ''))})" for col in schema_info[:20]])
        
        plan: List[str] = []
        if llm_provider.is_configured():
            prompt = f"""You are the Supervisor Agent in an autonomous data analyst system.
User Query: "{query}"
Target Table: "{table_name}"
Available Columns: {columns_desc}

Formulate a concise step-by-step analytical plan (3-5 steps) to answer the user request using SQL and statistical calculations.
Return a JSON object with:
"plan": ["Step 1: ...", "Step 2: ...", "Step 3: ...", "Step 4: ..."]
"""
            res = await llm_provider.generate_json(prompt)
            if res and "plan" in res and isinstance(res["plan"], list):
                plan = res["plan"]

        if not plan:
            # Deterministic default plan
            plan = [
                "1. Profile relevant column distributions and check data quality",
                f"2. Formulate analytical SQL queries against table '{table_name}'",
                "3. Compute aggregations and identify key patterns",
                "4. Independently verify all numerical calculations and extract evidence",
                "5. Render interactive visualizations and synthesize findings"
            ]

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        timeline_step = {
            "id": f"step_supervisor_{int(time.time()*1000)}",
            "agent": "Supervisor",
            "action": "Formulated execution plan and selected agents",
            "input_summary": f"Inquiry: {query}",
            "output_summary": f"Generated {len(plan)}-step plan",
            "status": "completed",
            "duration_ms": elapsed_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {"plan": plan}
        }

        current_timeline = list(state.get("timeline", []))
        current_timeline.append(timeline_step)

        return {
            "plan": plan,
            "current_agent": "Data Quality Agent",
            "timeline": current_timeline,
            "status": "running"
        }
