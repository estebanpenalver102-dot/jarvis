from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

class Settings(BaseSettings):
    environment: str = "development"
    # LLM — primary
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # LLM — free fallbacks
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    groq_api_key: Optional[str] = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    ollama_base_url: str = "http://host.docker.internal:11434"
    # DB — Render provides DATABASE_URL as postgresql://..., we need postgresql+asyncpg://
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
        # Render provides postgresql:// or postgres://, asyncpg needs postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+asyncpg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
