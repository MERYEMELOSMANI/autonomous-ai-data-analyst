import time
from typing import Dict, Any, List
from app.agents.state import AnalystState
from app.agents.llm_client import llm_provider

class ReportAgent:
    @classmethod
    async def run(cls, state: AnalystState) -> Dict[str, Any]:
        """
        Report Agent:
        Synthesizes the verified analytical results, visualizations, and quality audits
        into a coherent executive report and conversational response with evidence references.
        """
        start_time = time.perf_counter()
        query = state.get("query", "")
        dataset_name = state.get("dataset_name", "Dataset")
        findings = state.get("findings", [])
        quality_notes = state.get("data_quality_notes", [])
        evidence_records = state.get("evidence_records", [])
        visualizations = state.get("visualizations", [])

        # Construct structured markdown response
        response_lines = [
            f"### Analysis Overview: {dataset_name}\n",
            f"**Query**: *\"{query}\"*\n"
        ]

        if findings:
            response_lines.append("#### Verified Findings")
            for idx, f in enumerate(findings, 1):
                ev_id = f.get("evidence_id", "")
                verified_badge = "✅ **[Verified]**" if f.get("verified", True) else "⚠️ **[Discrepancy Detected]**"
                response_lines.append(f"{idx}. {verified_badge} **{f.get('title')}**\n   {f.get('description')}")
                if ev_id:
                    response_lines.append(f"   *(Evidence ID: `{ev_id}` — inspect in Evidence panel)*")
            response_lines.append("")

        if quality_notes:
            response_lines.append("#### Data Quality & Integrity Caveats")
            for note in quality_notes[:3]:
                response_lines.append(f"- {note}")
            response_lines.append("")

        response_lines.append("#### Methodology & Guardrails")
        response_lines.append(
            "- Calculations executed deterministically via DuckDB AST-validated SQL engine.\n"
            "- Quantitative figures verified independently by the Insight Verification Agent.\n"
            "- *Note: Observed associations represent statistical patterns in this sample and do not establish direct causation.*"
        )

        final_text = "\n".join(response_lines)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        timeline_step = {
            "id": f"step_report_{int(time.time()*1000)}",
            "agent": "Report Agent",
            "action": "Synthesized executive findings and verifiable report",
            "input_summary": f"Compiled {len(findings)} verified findings and {len(visualizations)} charts",
            "output_summary": "Final report generated with methodology and limitations",
            "tool_name": "executive_report_compiler",
            "status": "completed",
            "duration_ms": elapsed_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {
                "findings_count": len(findings),
                "charts_count": len(visualizations),
                "evidence_count": len(evidence_records)
            }
        }

        current_timeline = list(state.get("timeline", []))
        current_timeline.append(timeline_step)

        report_sections = {
            "title": f"Analysis: {query[:60]}",
            "objective": query,
            "executive_summary": "\n".join([f.get("description", "") for f in findings]),
            "methodology": "Deterministic DuckDB read-only SQL aggregation with automated verification loop.",
            "findings": findings,
            "limitations": quality_notes + ["Analysis does not imply causal inference beyond observational data."],
            "conclusions": [f.get("title", "") for f in findings]
        }

        return {
            "final_response": final_text,
            "report_sections": report_sections,
            "status": "completed",
            "timeline": current_timeline,
        }
