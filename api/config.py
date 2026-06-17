from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://jarvis:jarvis_secret@localhost:5432/jarvis_db"

    # LLM
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # LiveKit
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""

    # Auth
    jwt_secret: str = "dev_secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
