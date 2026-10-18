from typing import AsyncGenerator, Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from app.agents.state import AnalystState
from app.agents.supervisor import SupervisorAgent
from app.agents.data_quality import DataQualityAgent
from app.agents.data_analysis import DataAnalysisAgent
from app.agents.verification import InsightVerificationAgent
from app.agents.visualization import VisualizationAgent
from app.agents.report_agent import ReportAgent

def verification_router(state: AnalystState) -> Literal["data_analysis", "visualization"]:
    """Route back to data_analysis if verification failed and retries remain, otherwise proceed."""
    if state.get("needs_revision", False) and state.get("retry_count", 0) <= 1:
        return "data_analysis"
    return "visualization"

def build_analyst_graph():
    """Build and compile the LangGraph multi-agent execution workflow."""
    workflow = StateGraph(AnalystState)

    # Register agent nodes
    workflow.add_node("supervisor", SupervisorAgent.run)
    workflow.add_node("data_quality", DataQualityAgent.run)
    workflow.add_node("data_analysis", DataAnalysisAgent.run)
    workflow.add_node("verification", InsightVerificationAgent.run)
    workflow.add_node("visualization", VisualizationAgent.run)
    workflow.add_node("report", ReportAgent.run)

    # Define edges
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "data_quality")
    workflow.add_edge("data_quality", "data_analysis")
    workflow.add_edge("data_analysis", "verification")
    
    # Conditional edge with bounded retry loop
    workflow.add_conditional_edges(
        "verification",
        verification_router,
        {
            "data_analysis": "data_analysis",
            "visualization": "visualization"
        }
    )

    workflow.add_edge("visualization", "report")
    workflow.add_edge("report", END)

    return workflow.compile()

analyst_graph = build_analyst_graph()

async def stream_agent_workflow(initial_state: AnalystState) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream live agent execution events node-by-node.
    Yields timeline steps and intermediate state updates for SSE.
    """
    state = dict(initial_state)
    state.setdefault("timeline", [])
    state.setdefault("sql_queries", [])
    state.setdefault("query_results", [])
    state.setdefault("evidence_records", [])
    state.setdefault("visualizations", [])
    state.setdefault("findings", [])
    state.setdefault("retry_count", 0)

    # Supervisor step
    yield {"event": "step_start", "agent": "Supervisor", "status": "running"}
    supervisor_res = await SupervisorAgent.run(state)
    state.update(supervisor_res)
    yield {"event": "step_complete", "step": state["timeline"][-1], "plan": state.get("plan", [])}

    # Data Quality step
    yield {"event": "step_start", "agent": "Data Quality Agent", "status": "running"}
    quality_res = await DataQualityAgent.run(state)
    state.update(quality_res)
    yield {"event": "step_complete", "step": state["timeline"][-1]}

    # Data Analysis step
    yield {"event": "step_start", "agent": "Data Analysis Agent", "status": "running"}
    analysis_res = await DataAnalysisAgent.run(state)
    state.update(analysis_res)
    yield {"event": "step_complete", "step": state["timeline"][-1], "queries": state.get("sql_queries", [])}

    # Insight Verification step
    yield {"event": "step_start", "agent": "Insight Verification Agent", "status": "running"}
    verify_res = await InsightVerificationAgent.run(state)
    state.update(verify_res)
    yield {"event": "step_complete", "step": state["timeline"][-1], "evidence": state.get("evidence_records", [])}

    # Handle retry if verification failed
    if state.get("needs_revision", False) and state.get("retry_count", 0) <= 1:
        yield {"event": "step_start", "agent": "Data Analysis Agent", "action": "Revision after verification flag", "status": "running"}
        analysis_res = await DataAnalysisAgent.run(state)
        state.update(analysis_res)
        yield {"event": "step_complete", "step": state["timeline"][-1]}
        
        # Re-verify
        verify_res = await InsightVerificationAgent.run(state)
        state.update(verify_res)
        yield {"event": "step_complete", "step": state["timeline"][-1]}

    # Visualization step
    yield {"event": "step_start", "agent": "Visualization Agent", "status": "running"}
    viz_res = await VisualizationAgent.run(state)
    state.update(viz_res)
    yield {"event": "step_complete", "step": state["timeline"][-1], "visualizations": state.get("visualizations", [])}

    # Report step
    yield {"event": "step_start", "agent": "Report Agent", "status": "running"}
    report_res = await ReportAgent.run(state)
    state.update(report_res)
    yield {"event": "step_complete", "step": state["timeline"][-1]}

    # Final workflow completion event
    yield {
        "event": "workflow_finished",
        "final_response": state.get("final_response", ""),
        "evidence": state.get("evidence_records", []),
        "visualizations": state.get("visualizations", []),
        "timeline": state.get("timeline", []),
        "report_sections": state.get("report_sections", {})
    }
