from pydantic_settings import BaseSettings
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
    # DB
    database_url: str = "postgresql+asyncpg://jarvis:jarvis_secret@postgres:5432/jarvis"
    redis_url: str = "redis://redis:6379/0"
    # Auth
    secret_key: str = "change-me"
    api_key_header: str = "X-JARVIS-Key"
    # Integrations
    serpapi_key: Optional[str] = None
    spotify_client_id: Optional[str] = None
    spotify_client_secret: Optional[str] = None
    dealcenter_api_url: Optional[str] = None
    dealcenter_api_key: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
