from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.agents.llm_client import llm_provider

router = APIRouter()

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    observability_enabled: Optional[bool] = None

@router.get("")
async def get_system_settings():
    """Retrieve active system configuration and integration status."""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ai_provider": settings.AI_PROVIDER,
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_configured": llm_provider.is_configured(),
        "database_url": settings.DATABASE_URL.split("///")[-1],
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024),
        "allowed_extensions": settings.ALLOWED_EXTENSIONS,
        "observability_enabled": settings.ENABLE_OBSERVABILITY,
        "langfuse_configured": bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)
    }

@router.post("")
async def update_system_settings(req: SettingsUpdateRequest):
    """Update runtime configuration (e.g. configure Gemini API key) and persist to .env."""
    if req.gemini_api_key is not None:
        settings.GEMINI_API_KEY = req.gemini_api_key.strip()
        llm_provider.api_key = settings.GEMINI_API_KEY
        llm_provider._client = None
    if req.gemini_model is not None:
        settings.GEMINI_MODEL = req.gemini_model.strip()
        llm_provider.model_name = settings.GEMINI_MODEL
        llm_provider._client = None
    if req.observability_enabled is not None:
        settings.ENABLE_OBSERVABILITY = req.observability_enabled

    # Persist to .env
    try:
        from app.core.config import BASE_DIR
        env_file = BASE_DIR / ".env"
        env_vars = {}
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
        if settings.GEMINI_API_KEY:
            env_vars["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
        if settings.GEMINI_MODEL:
            env_vars["GEMINI_MODEL"] = settings.GEMINI_MODEL
        env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items()]) + "\n"
        env_file.write_text(env_content, encoding="utf-8")
    except Exception as e:
        pass

    return {
        "message": "Settings updated successfully",
        "gemini_configured": llm_provider.is_configured(),
        "gemini_model": settings.GEMINI_MODEL,
        "observability_enabled": settings.ENABLE_OBSERVABILITY
    }
