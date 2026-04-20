"""
Application configuration using Pydantic Settings
"""

import json
import logging
import os
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.demo_dataset import (
    DEMO_DATASET_NAME as DEFAULT_DEMO_DATASET_NAME,
    DEMO_DATASET_ORG_NAME as DEFAULT_DEMO_ORG_NAME,
    DEMO_DATASET_USER_EMAIL as DEFAULT_DEMO_USER_EMAIL,
    DEMO_DATASET_VERSION as DEFAULT_DEMO_DATASET_VERSION,
)
from app.modules.ai.services.model_catalog import get_default_provider_model


def _load_version_from_metrics() -> str:
    """Load app version from metrics.json (single source of truth)"""
    metrics_paths = [
        Path(__file__).parent.parent.parent.parent / "metrics.json",
    ]

    for metrics_path in metrics_paths:
        if metrics_path.exists():
            try:
                with open(metrics_path) as f:
                    metrics = json.load(f)
                    return metrics.get("version", {}).get("app", "0.2.0")
            except (OSError, json.JSONDecodeError):
                continue

    return "0.2.0"  # Failsafe default


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Bijmantra"
    APP_VERSION: str = _load_version_from_metrics()
    BRAPI_VERSION: str = "2.1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False  # Set to False in production

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

    # Rate Limiting Security
    # Token required to reset rate limits (only available in DEBUG mode)
    RATE_LIMIT_RESET_TOKEN: str | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate critical credentials in production
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY:
                raise ValueError(
                    "CRITICAL: SECRET_KEY must be set in production! "
                    'Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"'
                )
            if self.POSTGRES_PASSWORD == "changeme_in_production":
                raise ValueError("CRITICAL: POSTGRES_PASSWORD must be set in production!")
            if self.MINIO_ROOT_PASSWORD == "minioadmin123":
                raise ValueError("CRITICAL: MINIO_ROOT_PASSWORD must be set in production!")
            if not self.FIRST_SUPERUSER_PASSWORD or self.FIRST_SUPERUSER_PASSWORD == "Admin123!":
                raise ValueError(
                    "CRITICAL: FIRST_SUPERUSER_PASSWORD must be set to a secure value in production! "
                    "Set ADMIN_PASSWORD environment variable."
                )
            if self.SEED_DEMO_DATA:
                raise ValueError("CRITICAL: SEED_DEMO_DATA must be False in production!")
        else:
            if not self.SECRET_KEY:
                logger = logging.getLogger("app.core.config")
                random_key = secrets.token_urlsafe(32)
                object.__setattr__(self, "SECRET_KEY", random_key)
                logger.warning(
                    "SECRET_KEY not set. Using temporary random key. "
                    "Sessions will not persist across restarts. "
                    "Set SECRET_KEY in .env to fix this."
                )

            if not self.FIRST_SUPERUSER_PASSWORD:
                object.__setattr__(self, "FIRST_SUPERUSER_PASSWORD", "Admin123!")

            if not self.FIRST_DEMO_PASSWORD:
                object.__setattr__(self, "FIRST_DEMO_PASSWORD", "Demo123!")

        # Set default reset token for development if not provided
        if self.DEBUG and not self.RATE_LIMIT_RESET_TOKEN:
            object.__setattr__(self, 'RATE_LIMIT_RESET_TOKEN', "dev-reset-token")

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000

    # Seeding Configuration
    # Controls whether demo data seeders run (set to False in production)
    SEED_DEMO_DATA: bool = False
    DEMO_DATASET_NAME: str = DEFAULT_DEMO_DATASET_NAME
    DEMO_DATASET_VERSION: str = DEFAULT_DEMO_DATASET_VERSION
    DEMO_ORG_NAME: str = DEFAULT_DEMO_ORG_NAME
    DEMO_USER_EMAIL: str = DEFAULT_DEMO_USER_EMAIL

    # Initial Credentials (used by seeders)
    FIRST_SUPERUSER: str = "admin@bijmantra.org"
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    FIRST_DEMO_USER: str = DEFAULT_DEMO_USER_EMAIL
    FIRST_DEMO_PASSWORD: str = os.getenv("DEMO_PASSWORD", "")

    # Server Configuration (used by docker/deployment)
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    VITE_API_BASE_URL: str = "http://localhost:8000"
    DEVELOPER_CONTROL_PLANE_RUNTIME_ARTIFACTS_DIR: str | None = None

    # Meilisearch (optional search engine)
    MEILISEARCH_HOST: str = "http://localhost:7700"
    MEILISEARCH_API_KEY: str = ""

    # Security Configuration
    TRUSTED_PROXIES: list[str] = []  # List of trusted proxy IPs or CIDRs

    # AI / LLM Configuration
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = get_default_provider_model("groq", "meta-llama/llama-4-scout-17b-16e-instruct")

    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = get_default_provider_model("ollama", "llama3.2:3b")

    GOOGLE_AI_KEY: str | None = None
    GOOGLE_MODEL: str = get_default_provider_model("google", "gemini-flash-latest")

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = get_default_provider_model("openai", "gpt-4.1-mini")

    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str = get_default_provider_model("anthropic", "claude-3-7-sonnet-latest")

    HUGGINGFACE_API_KEY: str | None = None
    HF_MODEL: str = get_default_provider_model("huggingface", "mistralai/Mistral-7B-Instruct-v0.2")

    FUNCTIONGEMMA_API_KEY: str | None = None

    MEM0_ENABLED: bool = False
    MEM0_API_KEY: str | None = None
    MEM0_HOST: str = "https://api.mem0.ai"
    MEM0_ORG_ID: str | None = None
    MEM0_PROJECT_ID: str | None = None

    REEVU_LLM_PROVIDER: str | None = None
    VEENA_LLM_PROVIDER: str | None = None

    JULES_API_KEY: str | None = None

    # Weather API (Open-Meteo does not require a key)
    # GOOGLE_MAPS_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=["../.env", ".env"],  # Check root first, then current dir
        case_sensitive=True,
        extra="ignore",
    )


# Create settings instance
settings = Settings()
