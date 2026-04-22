"""
Runtime configuration (12-factor; env-driven). Single source-of-truth for every
micro-service inside the mono-repo.
"""
from functools import lru_cache
from pathlib import Path
from typing import List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field, field_validator

_ROOT = Path(__file__).resolve().parents[2]  # repo root

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # --- FastAPI ---
    APP_NAME: str = "AI-Analytics Platform"
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    WORKERS: int = Field(default=4)

    # --- Postgres ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://analytics:analytics@localhost:5432/analytics"
    )
    DB_POOL_SIZE: int = Field(default=20)

    # --- Redis ---
    REDIS_URL: str = Field(default="redis://localhost:6379")
    CELERY_TASK_ALWAYS_EAGER: bool = Field(default=False)

    # --- Security ---
    SECRET_KEY: str = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRE_MINUTES: int = Field(default=30)

    # --- AI ---
    # Accept the legacy OpenAI env names during the cutover so existing
    # deployments keep booting while Gemini becomes the primary runtime.
    GEMINI_API_KEY: str = Field(
        default="replace-me",
        validation_alias=AliasChoices("GEMINI_API_KEY", "OPENAI_API_KEY"),
    )
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices("GEMINI_MODEL", "OPENAI_MODEL"),
    )
    MAX_TOKENS: int = Field(default=2048)
    TEMPERATURE: float = Field(default=0.2)

    # --- ETL ---
    MAX_WORKERS: int = Field(default=8)
    BATCH_SIZE: int = Field(default=1000)
    CHUNK_SIZE: int = Field(default=10_000)

    ALLOWED_ORIGINS: List[str] = Field(default=["*"])

    # --- misc ---
    LOG_LEVEL: str = Field(default="INFO")
    CACHE_TTL: int = Field(default=3_600)
    UPLOADS_DIR: str = Field(default=str(_ROOT / "data" / "uploads"))

    @field_validator("DEBUG", mode="before")
    @classmethod
    def validate_debug(cls, v: bool | str) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production"}:
                return False
        raise ValueError("DEBUG must be a boolean or an accepted mode string")

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return cls._normalize_database_url("postgresql+asyncpg://" + v[len("postgres://") :])
        if v.startswith("postgresql://"):
            return cls._normalize_database_url("postgresql+asyncpg://" + v[len("postgresql://") :])
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must be a Postgres URL")
        return cls._normalize_database_url(v)
    
    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with redis://")
        return v

    @field_validator("UPLOADS_DIR")
    @classmethod
    def validate_uploads_dir(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("UPLOADS_DIR must not be empty")
        return v

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def validate_allowed_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            stripped = v.strip()
            if stripped == "*":
                return ["*"]
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        raise ValueError("ALLOWED_ORIGINS must be a list or comma-separated string")

    @staticmethod
    def _normalize_database_url(v: str) -> str:
        parsed = urlparse(v)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        normalized_pairs: list[tuple[str, str]] = []

        for key, value in query_pairs:
            if key == "sslmode":
                normalized_pairs.append(("ssl", value))
            else:
                normalized_pairs.append((key, value))

        return urlunparse(parsed._replace(query=urlencode(normalized_pairs)))

@lru_cache
def get_settings() -> Settings:
    return Settings()
