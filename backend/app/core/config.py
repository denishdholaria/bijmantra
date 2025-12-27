"""
Application configuration using Pydantic Settings
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "Bijmantra"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    
    # Demo Organization Configuration
    # Demo data is sandboxed in "Demo Organization" - completely isolated from production
    # Demo users log into this organization and see only demo data
    DEMO_ORG_NAME: str = "Demo Organization"
    DEMO_USER_EMAIL: str = "demo@bijmantra.org"
    DEMO_USER_PASSWORD: str = "demo123"
    
    # Demo Mode Configuration
    # DEMO_MODE: When True, enables demo features and fallback data
    # FEATURE_DEMO_DATA: When True, allows seeding demo data
    DEMO_MODE: bool = True
    FEATURE_DEMO_DATA: bool = True
    
    # Seeding Configuration
    # When True: `make db-seed` will populate Demo Organization with sample data
    SEED_DEMO_DATA: bool = True
    
    # API
    API_V2_PREFIX: str = "/brapi/v2"
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "bijmantra_user"
    POSTGRES_PASSWORD: str = "changeme_in_production"
    POSTGRES_DB: str = "bijmantra_db"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL"""
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
    MINIO_USE_SSL: bool = False
    
    # Security
    SECRET_KEY: str = "changeme_generate_random_secret_key_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000
    
    # Server Configuration (used by docker/deployment)
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    VITE_API_BASE_URL: str = "http://localhost:8000"
    
    # Meilisearch (optional search engine)
    MEILISEARCH_HOST: str = "http://localhost:7700"
    MEILISEARCH_API_KEY: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Create settings instance
settings = Settings()
