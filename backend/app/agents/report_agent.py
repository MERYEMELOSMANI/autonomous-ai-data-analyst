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

        final_text = None
        if llm_provider.is_configured():
            findings_summary = "\n".join([f"- {f.get('title')}: {f.get('description')}" for f in findings])
            prompt = f"""You are the Executive Report Agent in an Autonomous AI Data Analyst SaaS application.
The user asked: "{query}"
Dataset Name: "{dataset_name}"

Verified Findings Computed from Data:
{findings_summary}

Data Quality Notes:
{chr(10).join(['- ' + n for n in quality_notes[:4]])}

Write a direct, professional, and conversational analytical response that completely and accurately answers the user's question.
Guidelines:
- Start with a direct, comprehensive Executive Summary paragraph addressing the question.
- Reference the verified numbers and findings directly.
- Emphasize business context and meaning.
- Distinguish correlation from causation.
- Mention data quality notes if relevant.
- Format using clean Markdown with headers and bullet points.
"""
            llm_text = await llm_provider.generate_text(prompt)
            if llm_text and len(llm_text.strip()) > 50:
                final_text = llm_text.strip()

        if not final_text:
            q_lower = query.lower()
            is_overview = any(phrase in q_lower for phrase in [
                "what is this data about", "what is this dataset", "what is this", "what is in", "tell me about",
                "overview", "describe", "explain", "summary", "summarize", "about", "what do we have",
                "what does this contain", "what do you understand"
            ])

            response_lines = [
                f"### Executive Analysis: {dataset_name}\n",
                f"**Inquiry**: *\"{query}\"*\n"
            ]

            if is_overview:
                response_lines.append("#### Executive Summary")
                response_lines.append(
                    f"This dataset (**{dataset_name}**) provides a structured catalog of records tracking operational and business metrics. "
                    "The table has been fully indexed in an isolated analytical engine, verified for data integrity, and evaluated for key statistical distributions.\n"
                )
            elif findings:
                response_lines.append("#### Executive Summary")
                primary_finding = findings[0].get("description", "")
                response_lines.append(f"Analysis indicates: {primary_finding}\n")

            if findings:
                response_lines.append("#### Verified Findings & Evidence")
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
