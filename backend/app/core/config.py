"""
Application configuration using Pydantic Settings
"""

import json
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_version_from_metrics() -> str:
    """Load app version from metrics.json (single source of truth)"""
    metrics_paths = [
        Path(__file__).parent.parent.parent.parent / "metrics.json",  # /metrics.json (root)
        Path(__file__).parent.parent.parent.parent / ".kiro" / "metrics.json",  # legacy
    ]
    
    for metrics_path in metrics_paths:
        if metrics_path.exists():
            try:
                with open(metrics_path, "r") as f:
                    metrics = json.load(f)
                    return metrics.get("version", {}).get("app", "0.2.0")
            except (json.JSONDecodeError, IOError):
                continue
    
    return "0.2.0"  # Failsafe default


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Bijmantra"
    APP_VERSION: str = _load_version_from_metrics()
    BRAPI_VERSION: str = "2.1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True  # Set to False in production
    
    # API
    API_V2_PREFIX: str = "/brapi/v2"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "bijmantra_user"
    POSTGRES_PASSWORD: str = "changeme_in_production"
    POSTGRES_DB: str = "bijmantra_db"
    USE_SQLITE: bool = False
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
        if self.USE_SQLITE:
            return "sqlite+aiosqlite:///./bijmantra.db"
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin123"
    MINIO_BUCKET: str = "bijmantra-images"
    MINIO_BUCKET_RAW: str = "bijmantra-raw"
    MINIO_BUCKET_NORMALIZED: str = "bijmantra-normalized"
    MINIO_BUCKET_CURATED: str = "bijmantra-curated"
    MINIO_BUCKET_METADATA: str = "bijmantra-metadata"
    MINIO_USE_SSL: bool = False
    
    # Security
    # CRITICAL: SECRET_KEY must be set via environment variable in production
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate SECRET_KEY in non-development environments
        if not self.SECRET_KEY:
            if self.ENVIRONMENT == "production":
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be set in production! "
                    "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            else:
                # Development fallback - generate a random key per session
                import secrets
                object.__setattr__(self, 'SECRET_KEY', secrets.token_urlsafe(64))
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    
    # Seeding Configuration
    # Controls whether demo data seeders run (set to False in production)
    SEED_DEMO_DATA: bool = True
    
    # Server Configuration (used by docker/deployment)
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    VITE_API_BASE_URL: str = "http://localhost:8000"
    
    # Meilisearch (optional search engine)
    MEILISEARCH_HOST: str = "http://localhost:7700"
    MEILISEARCH_API_KEY: str = ""

    # AI / LLM Configuration
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    GOOGLE_AI_KEY: Optional[str] = None
    GOOGLE_MODEL: str = "gemini-2.0-flash"
    
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-haiku-20240307"
    
    HUGGINGFACE_API_KEY: Optional[str] = None
    HF_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.2"
    
    FUNCTIONGEMMA_API_KEY: Optional[str] = None
    
    VEENA_LLM_PROVIDER: Optional[str] = None
    
    JULES_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=["../.env", ".env"],  # Check root first, then current dir
        case_sensitive=True,
        extra="ignore",
    )


# Create settings instance
settings = Settings()
