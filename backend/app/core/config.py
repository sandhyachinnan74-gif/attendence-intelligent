import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "AttendAI"
    APP_ENV: str = "development"
    SECRET_KEY: str = "attendai-super-secret-key-32chars-minimum-token"
    JWT_SECRET_KEY: str = "attendai-jwt-secret-key-32chars-minimum-token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://attendai:password@localhost:5432/attendai"
    SQLITE_DATABASE_URL: str = "sqlite+aiosqlite:///./attendai.db"
    USE_SQLITE_FALLBACK: bool = True

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_FAKEREDIS_FALLBACK: bool = True

    # LLM Settings
    LLM_PROVIDER: str = "mock"  # nvidia | groq | gemini | mock
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "mistralai/mistral-large-2407"

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # CORS & General
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://localhost:80"
    LOG_LEVEL: str = "INFO"
    WORKER_CONCURRENCY: int = 2
    UPLOAD_DIR: str = "./uploads"

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
