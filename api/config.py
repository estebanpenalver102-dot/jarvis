from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

class Settings(BaseSettings):
    environment: str = "development"
    # LLM — primary
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # LLM — NVIDIA (build.nvidia.com, OpenAI-compatible)
    nvidia_api_key: Optional[str] = None
    # LLM — free fallbacks
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    groq_api_key: Optional[str] = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    ollama_base_url: str = "http://host.docker.internal:11434"
    # DB — provider gives postgresql://... (Render) or postgresql://...?sslmode=require (Neon
    # and most managed Postgres hosts); we need postgresql+asyncpg://, and asyncpg's own ssl
    # kwarg instead of libpq's sslmode query param (asyncpg doesn't understand sslmode).
    database_url: str = "postgresql+asyncpg://jarvis:jarvis_secret@postgres:5432/jarvis"
    redis_url: Optional[str] = None
    # Auth
    secret_key: str = "change-me"
    api_key_header: str = "X-JARVIS-Key"
    # Integrations
    serpapi_key: Optional[str] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    dealcenter_api_url: Optional[str] = None
    dealcenter_api_key: Optional[str] = None

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Provider gives postgres:// or postgresql://, asyncpg needs postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # SQLAlchemy's asyncpg dialect forwards an unrecognized query key like
        # "sslmode" straight through as a kwarg to asyncpg.connect(), but asyncpg's
        # connect() has no "sslmode" parameter — only "ssl". asyncpg's own "ssl" kwarg
        # does accept the same mode strings (disable/allow/prefer/require/verify-ca/
        # verify-full), so the fix is renaming the key, not changing its value.
        parts = urlsplit(v)
        query = dict(parse_qsl(parts.query))
        mode = query.pop("sslmode", None)
        if mode:
            query["ssl"] = mode
        parts = parts._replace(query=urlencode(query))
        return urlunsplit(parts)

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
