import time
import uuid
from typing import Dict, Any, List
from app.agents.state import AnalystState

class VisualizationAgent:
    @classmethod
    async def run(cls, state: AnalystState) -> Dict[str, Any]:
        """
        Visualization Agent:
        Analyzes query results, selects the optimal chart type, and synthesizes
        interactive Plotly JSON specifications formatted for dark mode.
        """
        start_time = time.perf_counter()
        query_results = state.get("query_results", [])
        visualizations: List[Dict[str, Any]] = list(state.get("visualizations", []))

        if query_results:
            last_res = query_results[-1]
            rows = last_res.get("rows", [])
            cols = last_res.get("columns", [])

            if rows and len(cols) >= 2:
                viz_spec = cls._generate_plotly_spec(rows, cols, state.get("query", "Data Breakdown"))
                if viz_spec:
                    visualizations.append(viz_spec)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        timeline_step = {
            "id": f"step_viz_{int(time.time()*1000)}",
            "agent": "Visualization Agent",
            "action": "Generated interactive Plotly visualization specifications",
            "input_summary": f"Visualized query result with {len(rows) if query_results else 0} data points",
            "output_summary": f"Rendered {len(visualizations)} chart(s)",
            "tool_name": "plotly_engine",
            "status": "completed",
            "duration_ms": elapsed_ms,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {
                "chart_types": [v.get("chart_type") for v in visualizations],
                "viz_count": len(visualizations)
            }
        }

        current_timeline = list(state.get("timeline", []))
        current_timeline.append(timeline_step)

        return {
            "visualizations": visualizations,
            "current_agent": "Report Agent",
            "timeline": current_timeline,
        }

    @staticmethod
    def _generate_plotly_spec(rows: List[Dict[str, Any]], cols: List[str], title_context: str) -> Dict[str, Any]:
        """Generate a clean, professional dark-themed Plotly figure spec."""
        x_col = cols[0]
        y_col = cols[-1]

        # Extract values
        x_vals = [r.get(x_col) for r in rows[:25]]
        y_vals = [r.get(y_col) for r in rows[:25]]

        # Determine if x_vals look like dates/time
        is_date = any("date" in str(x_col).lower() or "month" in str(x_col).lower() or "year" in str(x_col).lower() or "day" in str(x_col).lower() for _ in [0])
        
        # Decide chart type
        if is_date:
            chart_type = "line"
            trace = {
                "type": "scatter",
                "mode": "lines+markers",
                "x": x_vals,
                "y": y_vals,
                "name": y_col,
                "line": {"color": "#38bdf8", "width": 3},
                "marker": {"size": 6, "color": "#0ea5e9"}
            }
        elif len(rows) <= 15:
            chart_type = "bar"
            trace = {
                "type": "bar",
                "x": x_vals,
                "y": y_vals,
                "name": y_col,
                "marker": {
                    "color": "#3b82f6",
                    "opacity": 0.9,
                    "line": {"color": "#60a5fa", "width": 1}
                }
            }
        else:
            chart_type = "scatter"
            trace = {
                "type": "scatter",
                "mode": "markers",
                "x": x_vals,
                "y": y_vals,
                "name": f"{x_col} vs {y_col}",
                "marker": {"size": 8, "color": "#10b981", "opacity": 0.8}
            }

        layout = {
            "title": {
                "text": f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
                "font": {"color": "#f8fafc", "size": 15, "family": "Inter, sans-serif"}
            },
            "paper_bgcolor": "rgba(0,0,0,0)",
            "plot_bgcolor": "rgba(0,0,0,0)",
            "margin": {"l": 50, "r": 30, "t": 50, "b": 60},
            "xaxis": {
                "title": {"text": x_col.replace('_', ' ').title(), "font": {"color": "#94a3b8", "size": 12}},
                "tickfont": {"color": "#94a3b8", "size": 11},
                "gridcolor": "rgba(148, 163, 184, 0.12)",
                "zerolinecolor": "rgba(148, 163, 184, 0.15)"
            },
            "yaxis": {
                "title": {"text": y_col.replace('_', ' ').title(), "font": {"color": "#94a3b8", "size": 12}},
                "tickfont": {"color": "#94a3b8", "size": 11},
                "gridcolor": "rgba(148, 163, 184, 0.12)",
                "zerolinecolor": "rgba(148, 163, 184, 0.15)"
            },
            "showlegend": False,
            "hovermode": "closest"
        }

        return {
            "id": f"viz_{uuid.uuid4().hex[:8]}",
            "title": f"{y_col.replace('_', ' ').title()} by {x_col.replace('_', ' ').title()}",
            "chart_type": chart_type,
            "description": f"Visual breakdown comparing {y_col} across {x_col} observations.",
            "plotly_figure": {
                "data": [trace],
                "layout": layout
            },
            "xAxis": x_col,
            "yAxis": y_col
        }
