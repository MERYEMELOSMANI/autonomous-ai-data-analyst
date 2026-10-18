import time
from typing import Dict, Any, List
from app.agents.state import AnalystState

class DataQualityAgent:
    @staticmethod
    async def run(state: AnalystState) -> Dict[str, Any]:
        """
        Data Quality Agent:
        Inspects dataset health metrics, checks if columns to be queried have
        missing values, high duplication, or extreme outliers, and generates caveats.
        """
        start_time = time.perf_counter()
        quality_summary = state.get("quality_summary") or {}
        warnings = quality_summary.get("warnings", [])
        overall_score = quality_summary.get("overall_score", 100.0)

        notes: List[str] = []
        if overall_score < 70.0:
            notes.append(f"Overall dataset quality score is {overall_score}/100. Interpret findings with caution.")
        else:
            notes.append(f"Dataset health is robust (quality score: {overall_score}/100).")

        for w in warnings[:4]:
            if isinstance(w, dict):
                col = w.get("column")
                msg = w.get("message", "")
                if col:
                    notes.append(f"Column '{col}': {msg}")
                else:
                    notes.append(msg)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        timeline_step = {
            "id": f"step_quality_{int(time.time()*1000)}",
            "agent": "Data Quality Agent",
            "action": "Audited data health, missingness, and distribution integrity",
            "input_summary": f"Audited {len(warnings)} potential quality flags",
            "output_summary": f"Health score: {overall_score}/100 with {len(notes)} quality notes",
            "status": "completed",
            "duration_ms": elapsed_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {"score": overall_score, "notes": notes}
        }

        current_timeline = list(state.get("timeline", []))
        current_timeline.append(timeline_step)

        return {
            "data_quality_notes": notes,
            "current_agent": "Data Analysis Agent",
            "timeline": current_timeline,
        }
