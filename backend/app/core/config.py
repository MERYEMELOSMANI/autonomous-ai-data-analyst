import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")
    PROJECT_NAME: str = "Autonomous AI Data Analyst"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Storage & DB
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    DUCKDB_DIR: Path = BASE_DIR / "data" / "duckdb"
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/data/analyst.db"
    
    # Security & Limits
    MAX_UPLOAD_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".parquet", ".xlsx", ".xls"]
    QUERY_TIMEOUT_SECONDS: int = 30
    MAX_RESULT_ROWS: int = 1000
    
    # AI / LLM Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_PROVIDER: str = "gemini"  # gemini, mock, offline
    TEMPERATURE: float = 0.1
    MAX_RETRIES: int = 2
    
    # Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    ENABLE_OBSERVABILITY: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

settings = Settings()

# Ensure runtime directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.DUCKDB_DIR.mkdir(parents=True, exist_ok=True)
