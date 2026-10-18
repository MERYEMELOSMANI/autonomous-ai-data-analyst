import pytest
import asyncio
from pathlib import Path
from app.tools.duckdb_tool import duckdb_tool
from app.tools.polars_tool import polars_tool
from app.agents.supervisor import SupervisorAgent
from app.agents.data_quality import DataQualityAgent
from app.agents.data_analysis import DataAnalysisAgent
from app.agents.verification import InsightVerificationAgent
from app.agents.visualization import VisualizationAgent
from app.agents.report_agent import ReportAgent
from app.agents.graph import analyst_graph, stream_agent_workflow

DATA_DIR = Path(__file__).resolve().parent.parent / "eval" / "benchmarks"

@pytest.fixture(scope="module")
def setup_dataset():
    sales_file = DATA_DIR / "sales_performance.csv"
    table_name = "test_agents_sales"
    duckdb_tool.register_dataset(table_name, sales_file, "csv")
    cols, quality, sample_rows = polars_tool.profile_dataset(sales_file, "csv")
    return {
        "table_name": table_name,
        "schema_info": [c.model_dump() for c in cols],
        "quality_summary": quality.model_dump(),
        "query": "Compare total revenue by category"
    }

@pytest.mark.asyncio
async def test_supervisor_planning(setup_dataset):
    state = {
        "query": setup_dataset["query"],
        "table_name": setup_dataset["table_name"],
        "schema_info": setup_dataset["schema_info"]
    }
    result = await SupervisorAgent.run(state)
    assert "plan" in result
    assert len(result["plan"]) >= 3
    assert result["current_agent"] == "Data Quality Agent"

@pytest.mark.asyncio
async def test_data_quality_audit(setup_dataset):
    state = {
        "quality_summary": setup_dataset["quality_summary"],
        "timeline": []
    }
    result = await DataQualityAgent.run(state)
    assert "data_quality_notes" in result
    assert len(result["data_quality_notes"]) > 0

@pytest.mark.asyncio
async def test_data_analysis_and_verification(setup_dataset):
    state = {
        "query": setup_dataset["query"],
        "table_name": setup_dataset["table_name"],
        "schema_info": setup_dataset["schema_info"],
        "timeline": []
    }
    analysis_res = await DataAnalysisAgent.run(state)
    assert "sql_queries" in analysis_res
    assert len(analysis_res["sql_queries"]) > 0
    assert "findings" in analysis_res
    assert len(analysis_res["findings"]) > 0

    state.update(analysis_res)

    # Test Verification Agent
    verify_res = await InsightVerificationAgent.run(state)
    assert "evidence_records" in verify_res
    assert len(verify_res["evidence_records"]) > 0
    
    # Check that at least one evidence record is verified
    verified_records = [e for e in verify_res["evidence_records"] if e["verification_status"] == "VERIFIED"]
    assert len(verified_records) > 0
    assert verified_records[0]["tool"] == "duckdb_sql"

@pytest.mark.asyncio
async def test_visualization_generation(setup_dataset):
    state = {
        "query": setup_dataset["query"],
        "query_results": [{
            "columns": ["category", "total_sales"],
            "rows": [
                {"category": "Electronics", "total_sales": 50000},
                {"category": "Apparel", "total_sales": 32000}
            ]
        }],
        "visualizations": [],
        "timeline": []
    }
    viz_res = await VisualizationAgent.run(state)
    assert "visualizations" in viz_res
    assert len(viz_res["visualizations"]) == 1
    viz = viz_res["visualizations"][0]
    assert viz["chart_type"] in ["bar", "scatter", "line"]
    assert "plotly_figure" in viz

@pytest.mark.asyncio
async def test_end_to_end_streaming_workflow(setup_dataset):
    initial_state = {
        "session_id": "test_sess_001",
        "workflow_id": "test_wf_001",
        "query": setup_dataset["query"],
        "dataset_id": "test_ds_001",
        "table_name": setup_dataset["table_name"],
        "dataset_name": "Sales Test",
        "schema_info": setup_dataset["schema_info"],
        "sample_rows": [],
        "quality_summary": setup_dataset["quality_summary"]
    }

    events = []
    async for event in stream_agent_workflow(initial_state):
        events.append(event)

    assert len(events) >= 6
    workflow_finished = next(e for e in events if e.get("event") == "workflow_finished")
    assert "final_response" in workflow_finished
    assert "evidence" in workflow_finished
    assert "visualizations" in workflow_finished
    assert len(workflow_finished["timeline"]) >= 5
