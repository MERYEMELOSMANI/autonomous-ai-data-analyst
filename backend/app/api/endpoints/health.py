from fastapi import APIRouter
from app.core.config import settings
from app.agents.llm_client import llm_provider
from app.tools.duckdb_tool import duckdb_tool

router = APIRouter()

@router.get("/health")
async def health_check():
    """System health check and diagnostic status."""
    duckdb_healthy = True
    try:
        duckdb_tool.conn.execute("SELECT 1").fetchall()
    except Exception:
        duckdb_healthy = False

    return {
        "status": "healthy" if duckdb_healthy else "degraded",
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME,
        "duckdb_connected": duckdb_healthy,
        "ai_provider": settings.AI_PROVIDER,
        "gemini_configured": llm_provider.is_configured(),
        "gemini_model": settings.GEMINI_MODEL,
        "observability_enabled": settings.ENABLE_OBSERVABILITY
    }
